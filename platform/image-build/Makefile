# SURVIVE OS Image Build System
# Usage: make build-arm64, make build-amd64, make build-all, make clean

SHELL := /bin/bash
BUILD_SCRIPT := ./build.sh
OUTPUT_DIR := ./output
VARIANT ?= minimal

.PHONY: build-arm64 build-amd64 build-all clean checksums help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build-arm64: ## Build ARM64 (Raspberry Pi 4) image
	@echo "Building ARM64 image (variant: $(VARIANT))..."
	sudo $(BUILD_SCRIPT) --arch arm64 --variant $(VARIANT)

build-amd64: ## Build AMD64 (x86_64) image
	@echo "Building AMD64 image (variant: $(VARIANT))..."
	sudo $(BUILD_SCRIPT) --arch amd64 --variant $(VARIANT)

build-all: ## Build both ARM64 and AMD64 images (parallel)
	@echo "Building all images (variant: $(VARIANT))..."
	@$(MAKE) -j2 build-arm64 build-amd64

clean: ## Remove build artifacts and output
	rm -rf ./build ./output
	@echo "Build artifacts cleaned."

checksums: ## Generate SHA256 checksums for all images
	@if [ -d $(OUTPUT_DIR) ]; then \
		cd $(OUTPUT_DIR) && sha256sum *.img.xz 2>/dev/null > SHA256SUMS && \
		echo "Checksums written to $(OUTPUT_DIR)/SHA256SUMS" && \
		cat $(OUTPUT_DIR)/SHA256SUMS; \
	else \
		echo "No output directory found. Build images first."; \
	fi
