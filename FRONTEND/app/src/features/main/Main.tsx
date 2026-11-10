"use client"

import { Banner } from "./Pages/Banner"
import { HowToWork } from "./Pages/HowToWork"

export function Main() {

  return (
    <section className="h-[95%] pb-10">
      <Banner />
      <HowToWork />
    </section>
  )
}