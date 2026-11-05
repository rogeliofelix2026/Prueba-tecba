"use client"

import { Banner } from "./Pages/Banner"
import { HowToWork } from "./Pages/HowToWork"

export function Main() {

  return (
    <section className="h-screen">
      <Banner />
      <HowToWork />
    </section>
  )
}