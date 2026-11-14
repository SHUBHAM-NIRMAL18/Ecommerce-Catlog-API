"use client";

import { useRouter } from "next/navigation";
import { startTransition } from "react";

import { SecondaryLink, StateMessage } from "@/components/States";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const router = useRouter();

  const retry = () =>
    startTransition(() => {
      router.refresh();
      reset();
    });

  return (
    <div className="py-8">
      <StateMessage
        icon="alert"
        title="Something went wrong"
        message="We couldn't load the catalog just now. It may be a temporary problem, so please try again."
      >
        <button
          type="button"
          onClick={retry}
          className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-clay-700"
        >
          Try again
        </button>
        <SecondaryLink href="/">Back to all products</SecondaryLink>
      </StateMessage>
    </div>
  );
}
