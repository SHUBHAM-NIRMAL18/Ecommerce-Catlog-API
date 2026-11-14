import { PrimaryLink, SecondaryLink, StateMessage } from "@/components/States";

export default function NotFound() {
  return (
    <div className="py-8">
      <StateMessage
        icon="search"
        title="We couldn't find that page"
        message="The product or page you're looking for doesn't exist or is no longer available."
      >
        <PrimaryLink href="/">Browse all products</PrimaryLink>
        <SecondaryLink href="/collections">See collections</SecondaryLink>
      </StateMessage>
    </div>
  );
}
