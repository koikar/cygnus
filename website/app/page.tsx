import { Nav } from "@/components/sections/nav";
import { Hero } from "@/components/sections/hero";
import { Trust } from "@/components/sections/trust";
import { Problem } from "@/components/sections/problem";
import { Shift } from "@/components/sections/shift";
import { HowItWorks } from "@/components/sections/how-it-works";
import { Features } from "@/components/sections/features";
import { UseCase } from "@/components/sections/use-case";
import { Value } from "@/components/sections/value";
import { Faq } from "@/components/sections/faq";
import { Cta } from "@/components/sections/cta";
import { Footer } from "@/components/sections/footer";

export default function Home() {
  return (
    <>
      <Nav />
      <main className="flex flex-col">
        <Hero />
        <Trust />
        <Problem />
        <Shift />
        <HowItWorks />
        <Features />
        <UseCase />
        <Value />
        <Faq />
        <Cta />
      </main>
      <Footer />
    </>
  );
}
