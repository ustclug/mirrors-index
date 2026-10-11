export interface Repository {
  name: string;
  desc: string;
  updatedAt: string;
  helpUrl: string;
}

export interface DownloadGroup {
  distro: string;
  category: "os" | "app";
  urls: Array<{ name: string; url: string; size?: number }>;
}

export interface IndexDataV1 {
  schemaVersion: 1;
  generatedAt: string;
  repositories: Repository[];
  reverseProxies: Array<{ source: string; destination: string }>;
  downloads: DownloadGroup[];
  news: Array<{ title: string; url: string }>;
}

export interface SyncStatus {
  name: string;
  upstream: string;
  syncing: boolean;
  size: number;
  exitCode: number;
  lastSuccess: number;
  updatedAt: number;
  prevRun: number;
  nextRun: number;
}
