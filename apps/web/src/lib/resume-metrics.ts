export function estimateResumePages(
  bulletCount: number,
  sectionCount: number,
): number {
  const bulletLines = bulletCount * 1.5;
  const sectionOverhead = sectionCount * 2;
  const headerLines = 6;
  const totalLines = headerLines + bulletLines + sectionOverhead;
  return Math.max(1, Math.ceil(totalLines / 30));
}

export function getLengthGuidance(
  pages: number,
): { status: "good" | "warning" | "exceeded"; message: string } {
  if (pages <= 1) {
    return { status: "good", message: "Fits comfortably on 1 page." };
  }
  if (pages <= 2) {
    return {
      status: "warning",
      message: "May overflow to 2 pages. Consider removing less relevant experiences or reducing to 3–5 bullets per role.",
    };
  }
  return {
    status: "exceeded",
    message: "Likely exceeds 2 pages. Trim bullets or drop older roles to keep it concise.",
  };
}
