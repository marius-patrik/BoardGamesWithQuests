import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function mergeClassNames(...classes: ClassValue[]): string {
  return twMerge(clsx(classes));
}
