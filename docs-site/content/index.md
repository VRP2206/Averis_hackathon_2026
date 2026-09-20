---
layout: home
title: shipdoc docs
hero:
  name: shipdoc
  text: Shipping document checks you can trust
  tagline: Reads a shipping-documentation inbox, compares every draft Bill of Lading with its Shipping Instruction, and hands what it cannot decide to a person, with the reason.
  image:
    src: /logo.svg
    alt: shipdoc logo, an envelope riding a wave
  actions:
    - theme: brand
      text: Get started
      link: /guide/getting-started
    - theme: alt
      text: Open the app
      link: https://shipdoc.org
    - theme: alt
      text: API reference
      link: /reference/api
features:
  - icon: 🧮
    title: AI reads, code decides
    details: The comparison is plain, tested code. AI only helps read messy mail (classification fallback, field extraction, translation) and never decides a match.
    link: /concepts/how-it-works
    linkText: How it decides
  - icon: 🙋
    title: Escalates instead of guessing
    details: A missing attachment, an unreadable file, the wrong document type or a blank value goes to a person as Needs review, with the reason.
    link: /concepts/statuses
    linkText: Statuses and reasons
  - icon: 🔎
    title: Explains every decision
    details: A Why page for every email shows the words that classified it, each safety check, and the exact line each value was read from.
    link: /guide/user-guide
    linkText: User guide
  - icon: 📎
    title: Reads what people really send
    details: SI and BL attachments in .txt, .pdf, .docx and .xlsx, with the seven fields found whatever they are labelled ("POD" is "Port of Discharge").
    link: /concepts/statuses#the-seven-fields
    linkText: The seven fields
  - icon: 📥
    title: Your inbox or a sample
    details: Upload .eml files, or connect a mailbox over read-only IMAP. Thirteen ready-made test emails cover every case.
    link: /guide/test-emails
    linkText: Test emails
  - icon: 🌐
    title: Website, Android app and API
    details: One Python pipeline behind a React dashboard, an Android app built from the same code, and a documented HTTP API.
    link: /reference/api
    linkText: API reference
---
