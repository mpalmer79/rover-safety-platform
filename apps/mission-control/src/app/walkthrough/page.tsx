import { PageSurface } from "@/components/PageSurface";
import { ReviewerWalkthroughOverlay } from "@/reviewer/components/ReviewerWalkthroughOverlay";

export const dynamic = "force-static";

export default function WalkthroughPage() {
  return (
    <PageSurface>
      <ReviewerWalkthroughOverlay />
    </PageSurface>
  );
}
