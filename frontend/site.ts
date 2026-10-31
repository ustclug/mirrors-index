export interface Site {
  name: string;
  description?: string;
  logo?: string;
  footer?: string;
  announcement?: { label: string; url: string };
  domains?: Array<{ label: string; url: string }>;
  monitors?: Array<{ label: string; url: string }>;
  statusUrl?: string;
  links?: Array<{ label: string; url: string }>;
}
const element = document.getElementById("site-config");
export const site: Site | null = element
  ? JSON.parse(element.textContent || "null")
  : null;
