/**
 * The 3Gem lockup: the stylised "3" mark, then "Gem", then the product name.
 * The mark is the real asset from Cpi-Dashboard (public/favicon.svg), copied to
 * public/brand/3gem-mark.svg so both products show the same logo.
 */
export function BrandLockup({ product = "Project Hub" }: { product?: string }) {
  return (
    <span className="flex items-center gap-2">
      <img
        src="/brand/3gem-mark.svg"
        alt=""
        aria-hidden="true"
        className="size-7 rounded-[5px]"
        width={28}
        height={28}
      />
      <span className="text-[15px] tracking-[-0.01em]">
        <span className="font-semibold text-ink">Gem</span>{" "}
        <span className="font-normal text-ink-muted">{product}</span>
      </span>
    </span>
  );
}
