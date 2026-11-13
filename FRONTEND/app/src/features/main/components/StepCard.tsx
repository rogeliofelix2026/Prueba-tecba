'use client'

import { useRef, useState } from 'react'

interface ExtraItems {
  title: string
  description: string
}

interface Requirement {
  number: string
  title: string
  description: string
}

interface Items {
  requeriments?: Requirement[]
  extra?: ExtraItems[]
}

interface StepCardProps {
  number: string
  label: string
  title: string
  description: string
  tag?: string
  color?: "teal" | "blue" | "purple"
  items?: Items
  requirementsTitle?: string
  moreButtonOpen: string
  moreButtonClose: string
  footerNote?: string
  footerLink?: string
}

export function StepCard({
  number,
  label,
  title,
  description,
  tag,
  color = "teal",
  items,
  requirementsTitle,
  moreButtonOpen,
  moreButtonClose,
  footerNote,
  footerLink,
}: StepCardProps) {
  const [open, setOpen] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)

  const handleToggle = () => {
    const willOpen = !open
    setOpen(willOpen)

    if (willOpen) {
      // Esperar a que se expanda y después scrollear
      setTimeout(() => {
        cardRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        })
      }, 300)
    }
  }

  const colors = {
    teal: {
      label: "#035C80", //texto color 1
      tagText: "#035C80", //texto color 1
      footerNoteText: "#035C80", //texto color 1
      footerLinkText: "#035C80", //texto color 1

      pDescriptionText: "#527084", //texto color 2

      numberText: "#143146", //texto color 3
      buttonText: "#143146", //texto color 3
      pTitleText: "#143146", //texto color 3

      itemBadgeText: "#4fbb97",// texto color 4

      accent: "#038D84",//border top Color

      //Backgrounds
      bgCard: "#F9FFFD",
      numberBg: "linear-gradient(66.89deg, #A5E9E1 13.08%, #DCEBFF 106.54%)",
      tagBg: "#ECF4FC",
      buttonBg: "#E6F8F4",
      buttonHover: "#dbf7f1",
      itemBadgeBg: "#dbfaf0",
      expandedBg: "#F5F8FE",

      //borde
      border: "1px solid #BFE7E0",
      borderActive: "1px solid #038D84"
    },
    blue: {

      label: "#035C80", //texto color 1
      tagText: "#035C80", //texto color 1
      footerNoteText: "#035C80", //texto color 1
      footerLinkText: "#035C80", //texto color 1

      pDescriptionText: "#527084", //texto color 2

      numberText: "#143146", //texto color 3
      buttonText: "#143146", //texto color 3
      pTitleText: "#143146", //texto color 3

      itemBadgeText: "#3E64D5",// texto color 4

      accent: "#3D69DB",//border Top Color

      //Backgrounds
      bgCard: "#FAFCFF",
      numberBg: "#DCEBFF",
      tagBg: "#ECF4FC",
      buttonBg: "#E8F0FF",
      buttonHover: "#dbeafe",
      itemBadgeBg: "#E1EBF9",
      expandedBg: "#F5F8FE",

      //borde
      border: "1px solid #CAD8F7",
      borderActive: "1px solid #3D69DB"
    },
    purple: {
      label: "#035C80", //texto color 1
      tagText: "#035C80", //texto color 1
      footerNoteText: "#035C80", //texto color 1
      footerLinkText: "#035C80", //texto color 1

      pDescriptionText: "#527084", //texto color 2

      numberText: "#143146", //texto color 3
      buttonText: "#143146", //texto color 3
      pTitleText: "#143146", //texto color 3

      itemBadgeText: "#7552C6",// texto color 4

      accent: "#7552C6",//border top Color

      //Backgrounds
      bgCard: "#FCFAFF",
      numberBg: "linear-gradient(66.89deg, #D7C3FF 13.08%, #DCEBFF 106.54%)",
      tagBg: "#ECF4FC",
      buttonBg: "#F6F2FF",
      buttonHover: "#f0eafd",
      itemBadgeBg: "#efe7ff",
      expandedBg: "#F5F8FE",

      //borde
      border: "1px solid #DCD1F5",
      borderActive: "1px solid #7552C6"
    },
  }[color]

  const fonts = {
    archivo: "var(--font-archivo), sans-serif",
    openSans: "var(--font-opensans), sans-serif",
  }

  const type = {
    number: { fontFamily: fonts.archivo, fontSize: "25px", fontWeight: 700 },
    label: { fontFamily: fonts.openSans, fontSize: "11px", fontWeight: 600 },
    title: { fontFamily: fonts.archivo, fontSize: "17px", fontWeight: 600 },
    desc: { fontFamily: fonts.openSans, fontSize: "14px", fontWeight: 400 },
    tag: { fontFamily: fonts.openSans, fontSize: "12px", fontWeight: 500 },
    button: { fontFamily: fonts.openSans, fontSize: "14px", fontWeight: 500 },
    reqTitle: { fontFamily: fonts.archivo, fontSize: "14px", fontWeight: 600 },
    itemTitle: { fontFamily: fonts.archivo, fontSize: "14px", fontWeight: 600 },
    itemDesc: { fontFamily: fonts.openSans, fontSize: "14px", fontWeight: 400 },
    footer: { fontFamily: fonts.openSans, fontSize: "14px", fontWeight: 500 },
    itemBadge: { fontFamily: fonts.openSans, fontSize: "11px", fontWeight: 600 },
  }

  const hasRequirements = (items?.requeriments?.length ?? 0) > 0

  return (
    <div
      className="flex flex-col rounded-xl  bg-white p-5 shadow-sm border border-gray-100 border-t-[3px]"
            ref={cardRef}

      style={{ borderTopColor: colors.accent, backgroundColor: colors.bgCard }}
    >
      {/* Header */}
      <div className="mb-3 flex items-start gap-3">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center p-6 rounded-lg"
          style={{
            background: colors.numberBg,
            color: colors.numberText,
            ...type.number,
          }}
        >
          {number}
        </div>

        <div className="min-w-0">
          <p
            className="uppercase tracking-wider"
            style={{ color: colors.label, ...type.label }}
          >
            {label}
          </p>
          <h3 className="leading-tight text-gray-900" style={{ ...type.title, color: colors.pTitleText }}>
            {title}
          </h3>
        </div>
      </div>

      {/* Description */}
      <p className="mb-3 leading-relaxed text-gray-500" style={{ ...type.desc, color: colors.pDescriptionText }}>
        {description}
      </p>

      {/* Tag */}
      {tag && (
        <div className="mb-3">
          <span
            className="inline-block"
            style={{
              color: colors.tagText,
              ...type.tag,
            }}
          >
            {tag}
          </span>
        </div>
      )}

      {/* Toggle Button */}
      {hasRequirements && (
        <button
          onClick={handleToggle}
          className="flex w-full items-center gap-2.5 rounded-lg px-4 py-3 transition-colors"
          style={{
            backgroundColor: colors.buttonBg,
            color: colors.buttonText,
            border: open ? colors.borderActive : colors.border,
            ...type.button,
            cursor: "pointer",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = colors.buttonHover)}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = colors.buttonBg)}
        >
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-current text-xs leading-none">
            {open ? "−" : "+"}
          </span>
          <span>{open ? `${moreButtonClose}` : `${moreButtonOpen}`}</span>
        </button>
      )}

      {/* Expanded content */}
      {hasRequirements && (
        <div
          className="grid transition-[grid-template-rows] duration-300 ease-in-out"
          style={{ gridTemplateRows: open ? "1fr" : "0fr" }}
        >
          <div className="overflow-hidden">
            <div
              className="mt-4 rounded-lg p-4"
              style={{ backgroundColor: colors.expandedBg, border: "solid 1px #D8E4F3" }}
            >
              {requirementsTitle && (
                <h4 className="mb-5 text-gray-900" style={{ ...type.reqTitle, color: colors.pTitleText }}>
                  {requirementsTitle}
                </h4>
              )}

              <div className="flex flex-col gap-5">
                <>
                  {items.requeriments.map((req, i) => (
                    <div key={`${i}-req`} className="flex gap-3">
                      {
                        req.number &&
                        (<div
                          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
                          style={{
                            backgroundColor: colors.itemBadgeBg,
                            color: colors.itemBadgeText,
                            ...type.itemBadge,
                          }}
                        >
                          {req.number}
                        </div>)}

                      <div className="min-w-0">
                        <p className="text-gray-900" style={{ ...type.itemTitle, color: colors.pTitleText }}>
                          {req.title}
                        </p>
                        <p className="mt-0.5 leading-relaxed text-gray-500" style={{ ...type.itemDesc, color: colors.pDescriptionText }}>
                          {req.description}
                        </p>
                      </div>


                    </div>
                  ))}

                  {items.extra && items.extra.map((extra, i) => (
                    <div key={`${i}-extra`} className="min-w-0">
                      <p className="text-gray-900" style={{ ...type.itemTitle, color: colors.pTitleText }}>
                        {extra.title}
                      </p>
                      <p className="mt-0.5 leading-relaxed text-gray-500" style={{ ...type.itemDesc, color: colors.pDescriptionText }}>
                        {extra.description}
                      </p>
                    </div>
                  ))}
                </>
              </div>

              {footerNote && (
                <p className="mt-5 text-gray-700" style={{ ...type.footer, color: colors.footerNoteText }}>
                  {footerNote}
                </p>
              )}

              {footerLink && (
                <a
                  href={footerLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-blue-600 hover:underline"
                  style={{ ...type.footer, color: colors.footerLinkText }}
                >
                  Consultar la página oficial del trámite
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}