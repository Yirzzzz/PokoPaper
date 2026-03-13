import { getPaperTypeMeta } from "@/lib/pokedex";

type TypeChipProps = {
  value?: string | null;
  tags?: string[];
  className?: string;
};

export function TypeChip({ value, tags = [], className = "" }: TypeChipProps) {
  const meta = getPaperTypeMeta(value, tags);

  return (
    <span className={`rounded-full border px-3 py-1.5 text-sm ${meta.chipClassName} ${className}`}>
      {meta.label}
    </span>
  );
}
