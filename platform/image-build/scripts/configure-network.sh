#!/usr/bin/env bash
# configure-network.sh - Configure networking for SURVIVE OS
# Usage: configure-network.sh <rootfs_path>

set -euo pipefail

ROOTFS="${1:?Usage: configure-network.sh <rootfs_path>}"

echo "==> Configuring network for SURVIVE OS"

# Configure NetworkManager for WiFi AP + client mode
setup_networkmanager() {
    echo "  -> Configuring NetworkManager"
    local nm_dir="${ROOTFS}/etc/NetworkManager"
    mkdir -p "${nm_dir}/conf.d" "${nm_dir}/system-connections"

    cat > "${nm_dir}/NetworkManager.conf" << 'EOF'
[main]
plugins=keyfile
dns=default

[keyfile]
unmanaged-devices=none

[connectivity]
enabled=false

[device]
wifi.scan-rand-mac-address=no
EOF

    # WiFi AP fallback connection (activated if no known networks found)
    cat > "${nm_dir}/system-connections/survive-ap.nmconnection" << 'EOF'
[connection]
id=survive-ap
type=wifi
autoconnect=true
autoconnect-priority=-1

[wifi]
mode=ap
ssid=SURVIVE-NODE

[wifi-security]
key-mgmt=wpa-psk
psk=survive-setup

[ipv4]
method=shared
address1=10.42.0.1/24

[ipv6]
method=ignore
EOF
    chmod 600 "${nm_dir}/system-connections/survive-ap.nmconnection"
}

# Configure avahi/mDNS for survive.local
setup_avahi() {
    echo "  -> Configuring avahi/mDNS"
    local avahi_dir="${ROOTFS}/etc/avahi"
    mkdir -p "${avahi_dir}/services"

    cat > "${avahi_dir}/avahi-daemon.conf" << 'EOF'
[server]
host-name=survive-node
domain-name=local
use-ipv4=yes
use-ipv6=no
allow-interfaces=eth0,wlan0,end0

[wide-area]
enable-wide-area=no

[publish]
publish-addresses=yes
publish-hinfo=no
publish-workstation=no
publish-domain=yes

[reflector]
enable-reflector=yes

[rlimits]
rlimit-core=0
rlimit-data=4194304
rlimit-fsize=0
rlimit-nofile=768
rlimit-stack=4194304
rlimit-nproc=3
EOF

    # Publish SURVIVE OS web service via mDNS
    cat > "${avahi_dir}/services/survive-web.service" << 'EOF'
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">SURVIVE OS on %h</name>
  <service>
    <type>_http._tcp</type>
    <port>80</port>
    <txt-record>path=/</txt-record>
  </service>
</service-group>
EOF
}

# Configure nftables firewall
setup_firewall() {
    echo "  -> Configuring nftables firewall"
    local nft_dir="${ROOTFS}/etc/nftables.d"
    mkdir -p "${nft_dir}"

    cat > "${ROOTFS}/etc/nftables.conf" << 'EOF'
#!/usr/sbin/nft -f

flush ruleset

table inet survive_firewall {
    chain input {
        type filter hook input priority 0; policy drop;

        # Accept established/related connections
        ct state established,related accept

        # Accept loopback
        iifname "lo" accept

        # Accept ICMP/ping
        ip protocol icmp accept

        # SSH
        tcp dport 22 accept

        # HTTP/HTTPS (nginx proxy)
        tcp dport { 80, 443 } accept

        # mDNS
        udp dport 5353 accept

        # SURVIVE OS module ports (local network only)
        ip saddr 10.0.0.0/8 tcp dport 8000-8090 accept
        ip saddr 172.16.0.0/12 tcp dport 8000-8090 accept
        ip saddr 192.168.0.0/16 tcp dport 8000-8090 accept
        ip saddr 10.42.0.0/24 tcp dport 8000-8090 accept

        # LDAP (local only)
        ip saddr 127.0.0.0/8 tcp dport 3890 accept

        # Redis (local only)
        ip saddr 127.0.0.0/8 tcp dport 6379 accept

        # DHCP (for AP mode)
        udp dport 67 accept
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Allow forwarding for AP clients (NAT)
        iifname "wlan0" oifname "eth0" accept
        ct state established,related accept
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

table ip survive_nat {
    chain postrouting {
        type nat hook postrouting priority 100;
        oifname "eth0" masquerade
    }
}
EOF

    # Enable nftables service
    mkdir -p "${ROOTFS}/etc/systemd/system/multi-user.target.wants"
    ln -sf /lib/systemd/system/nftables.service \
        "${ROOTFS}/etc/systemd/system/multi-user.target.wants/nftables.service" 2>/dev/null || true
}

# Run all network configuration
setup_networkmanager
setup_avahi
setup_firewall

echo "==> Network configuration complete"
