/** Joins conditional class names. No tailwind-merge dependency — this
 * component set doesn't stack conflicting utilities on the same element
 * often enough to need conflict resolution, just conditional inclusion. */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}
