/**
 * Module registry - maps to the SURVIVE OS port map.
 * Each entry defines a module available in the sidebar.
 */
export const MODULES = [
  { id: 'identity', name: 'Identity Admin', port: 8001, icon: 'ID' },
  { id: 'comms', name: 'Communications', port: 8010, icon: 'CM' },
  { id: 'security', name: 'Security', port: 8020, icon: 'SC' },
  { id: 'agriculture', name: 'Agriculture', port: 8030, icon: 'AG' },
  { id: 'medical', name: 'Medical', port: 8040, icon: 'MD' },
  { id: 'resources', name: 'Resources', port: 8050, icon: 'RS' },
  { id: 'maps', name: 'Maps', port: 8060, icon: 'MP' },
  { id: 'governance', name: 'Governance', port: 8070, icon: 'GV' },
  { id: 'weather', name: 'Weather', port: 8080, icon: 'WX' },
  { id: 'education', name: 'Education', port: 8090, icon: 'ED' },
];
