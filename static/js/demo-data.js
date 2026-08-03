/**
 * All demo data for the UI. Nothing here talks to a server — every page
 * reads from window.DEMO synchronously. Replace with real API calls /
 * Django context data when the backend exists.
 */
window.DEMO = {
  user: {
    name: "Ananya Verma",
    email: "ananya.verma@lexora.law",
    initials: "AV",
    firm: "Verma & Associates",
    mfaEnabled: true,
  },

  kpis: {
    totalCases: 48,
    activeCases: 31,
    closedCases: 17,
    aiChatsWeek: 126,
    aiChatsDelta: 18,
  },

  cases: [
    {
      id: "crl-214-2024",
      number: "CRL/214/2024",
      title: "State vs. Sharma",
      type: "Criminal",
      client: "Rohit Sharma",
      opposite: "State of NCT of Delhi",
      court: "District Court, Delhi (Court Room 4)",
      judge: "Hon. Justice A. Rao",
      hearingDate: "2026-08-12",
      hearingTime: "10:30 AM",
      status: "active",
      documents: 12,
      description: "Assault case arising from an incident on 14 March 2024. Prosecution alleges use of a sharp-edged weapon; defense contends alibi supported by witness testimony.",
      updatedAt: "2h ago",
    },
    {
      id: "civ-89-2023",
      number: "CIV/89/2023",
      title: "Mehta Contract Dispute",
      type: "Civil",
      client: "Ashok Mehta",
      opposite: "Delta Infrastructure Pvt. Ltd.",
      court: "High Court of Delhi",
      judge: "Hon. Justice K. Nair",
      hearingDate: "2026-08-06",
      hearingTime: "2:00 PM",
      status: "hearing",
      documents: 7,
      description: "Breach of a construction supply contract. Dispute centers on amended clause 4.2 between contract v1 and v2.",
      updatedAt: "1d ago",
    },
    {
      id: "crl-77-2022",
      number: "CRL/77/2022",
      title: "Kumar Bail Application",
      type: "Criminal",
      client: "Vikram Kumar",
      opposite: "State of Maharashtra",
      court: "Sessions Court, Mumbai",
      judge: "Hon. Justice S. Deshmukh",
      hearingDate: "2026-08-11",
      hearingTime: "11:00 AM",
      status: "active",
      documents: 5,
      description: "Bail application pending investigation completion under Section 439 CrPC.",
      updatedAt: "3d ago",
    },
    {
      id: "arb-12-2025",
      number: "ARB/12/2025",
      title: "Rao Arbitration",
      type: "Arbitration",
      client: "Nandini Rao",
      opposite: "Skyline Developers",
      court: "Arbitration Tribunal, Bengaluru",
      judge: "Sole Arbitrator P. Iyengar",
      hearingDate: null,
      hearingTime: null,
      status: "active",
      documents: 21,
      description: "Commercial arbitration over delayed possession of a residential unit and penalty clause enforcement.",
      updatedAt: "5d ago",
    },
    {
      id: "civ-45-2024",
      number: "CIV/45/2024",
      title: "Iyer Property Title",
      type: "Civil",
      client: "Ramesh Iyer",
      opposite: "Chennai Municipal Corporation",
      court: "District Court, Chennai",
      judge: "Hon. Justice M. Balan",
      hearingDate: "2026-08-08",
      hearingTime: "9:30 AM",
      status: "hearing",
      documents: 9,
      description: "Property title dispute; OCR still processing scanned 1980s land records.",
      updatedAt: "6h ago",
    },
    {
      id: "crl-301-2021",
      number: "CRL/301/2021",
      title: "Verma Cheque Bounce",
      type: "Criminal",
      client: "Suresh Verma",
      opposite: "Neha Kapoor",
      court: "Metropolitan Court, Delhi",
      judge: "Hon. Justice R. Bhatt",
      hearingDate: null,
      hearingTime: null,
      status: "closed",
      documents: 14,
      description: "Section 138 Negotiable Instruments Act matter, resolved via settlement.",
      updatedAt: "2mo ago",
    },
  ],

  documents: {
    "crl-214-2024": [
      { id: "d1", name: "FIR_copy.pdf", type: "pdf", pages: 4, uploadedAt: "20 Mar 2024", ocr: "complete", size: "1.2 MB" },
      { id: "d2", name: "Postmortem_report.pdf", type: "pdf", pages: 8, uploadedAt: "22 Mar 2024", ocr: "complete", size: "3.4 MB" },
      { id: "d3", name: "Witness_01_statement.docx", type: "docx", pages: 3, uploadedAt: "25 Mar 2024", ocr: "n/a", size: "220 KB" },
      { id: "d4", name: "Witness_02_statement.docx", type: "docx", pages: 2, uploadedAt: "25 Mar 2024", ocr: "n/a", size: "180 KB" },
      { id: "d5", name: "Scene_photo_01.jpg", type: "img", pages: 1, uploadedAt: "26 Mar 2024", ocr: "processing", size: "4.8 MB" },
      { id: "d6", name: "Scene_photo_04.jpg", type: "img", pages: 1, uploadedAt: "26 Mar 2024", ocr: "complete", size: "5.1 MB" },
      { id: "d7", name: "Call_records.pdf", type: "pdf", pages: 12, uploadedAt: "02 Apr 2024", ocr: "complete", size: "890 KB" },
      { id: "d8", name: "Charge_sheet.pdf", type: "pdf", pages: 22, uploadedAt: "10 Apr 2024", ocr: "complete", size: "6.7 MB" },
    ],
    "civ-89-2023": [
      { id: "d9", name: "Contract_v1.docx", type: "docx", pages: 14, uploadedAt: "02 Jan 2023", ocr: "n/a", size: "410 KB" },
      { id: "d10", name: "Contract_v2.docx", type: "docx", pages: 15, uploadedAt: "18 Jun 2023", ocr: "n/a", size: "430 KB" },
      { id: "d11", name: "Delivery_logs.pdf", type: "pdf", pages: 6, uploadedAt: "01 Jul 2023", ocr: "complete", size: "1.1 MB" },
    ],
  },

  chats: {
    "crl-214-2024": [
      { role: "ai", text: "Hi Ananya — I've indexed all 12 documents for State vs. Sharma. Ask me anything about the case.", sources: [] },
      { role: "user", text: "What evidence supports the client's alibi?" },
      {
        role: "ai",
        text: "Witness A's statement places the accused at a family gathering between 9:15 and 10:30 PM on the night of the incident, which conflicts with the FIR's recorded timestamp of 9:40 PM. Call records submitted separately corroborate the witness account, showing an active call from the client's location at 9:42 PM.",
        sources: [
          { doc: "Witness_01_statement.docx", page: 2 },
          { doc: "FIR_copy.pdf", page: 1 },
          { doc: "Call_records.pdf", page: 5 },
        ],
        confidence: 0.91,
      },
      { role: "user", text: "Find all witness statements mentioning fingerprints." },
      {
        role: "ai",
        text: "Only one reference to fingerprints was found. Witness_02's statement notes that investigators dusted the recovered object but does not confirm a match to the accused.",
        sources: [{ doc: "Witness_02_statement.docx", page: 1 }],
        confidence: 0.78,
      },
    ],
  },

  summaries: {
    "crl-214-2024": {
      overview: "State vs. Sharma concerns an alleged assault on 14 March 2024. The prosecution's case rests primarily on the FIR and postmortem findings, while the defense has introduced an alibi supported by witness testimony and corroborating call records.",
      evidence: [
        { label: "FIR timestamp discrepancy", detail: "FIR records incident at 9:40 PM; client's call log places him elsewhere at 9:42 PM.", doc: "FIR_copy.pdf · p.1" },
        { label: "Postmortem weapon consistency", detail: "Injuries consistent with a sharp-edged instrument, matching prosecution's claim.", doc: "Postmortem_report.pdf · p.3" },
        { label: "Corroborating call record", detail: "Active call from client's registered number at time of incident.", doc: "Call_records.pdf · p.5" },
      ],
      witnesses: [
        { name: "Witness A (neighbor)", summary: "Places accused at family gathering 9:15–10:30 PM." },
        { name: "Witness B (shop owner)", summary: "Corroborates general FIR sequence of events near the scene." },
      ],
      pending: [
        "Chain-of-custody confirmation for the recovered weapon",
        "Reconciling FIR timeline against Witness A's alibi",
        "Cross-examination of Witness B scheduled for next hearing",
      ],
    },
  },

  timelines: {
    "crl-214-2024": [
      { date: "14 Mar 2024", title: "Incident occurred", desc: "Alleged assault reported near Lajpat Nagar market.", major: true, attach: "Scene_photo_04.jpg" },
      { date: "15 Mar 2024", title: "FIR filed", desc: "FIR registered at Lajpat Nagar police station, incident timestamp 9:40 PM.", major: true, attach: "FIR_copy.pdf" },
      { date: "18 Mar 2024", title: "Investigation started", desc: "Investigating officer assigned; scene photographs collected.", major: false, attach: null },
      { date: "22 Mar 2024", title: "Postmortem report filed", desc: "Medical examiner report submitted to investigating officer.", major: false, attach: "Postmortem_report.pdf" },
      { date: "25 Mar 2024", title: "Witness statements recorded", desc: "Two witness statements recorded, one supporting an alibi.", major: true, attach: "Witness_01_statement.docx" },
      { date: "10 Apr 2024", title: "Charge sheet filed", desc: "Charge sheet submitted to the District Court, Delhi.", major: true, attach: "Charge_sheet.pdf" },
      { date: "12 Aug 2026", title: "Next hearing", desc: "Cross-examination of Witness B scheduled.", major: true, attach: null },
    ],
  },

  notes: {
    "crl-214-2024": [
      { id: "n1", title: "Cross-examination prep", body: "Focus on the 9:40 vs 9:42 PM discrepancy. Prepare call log printout as exhibit.", ai: false, updatedAt: "Yesterday" },
      { id: "n2", title: "AI: Key contradictions", body: "AI-generated: FIR timestamp conflicts with call record; postmortem is consistent with prosecution's weapon claim but not with identity of assailant.", ai: true, updatedAt: "2 days ago" },
      { id: "n3", title: "Client meeting notes", body: "Client confirmed attendance at family gathering, provided names of 3 additional attendees to contact.", ai: false, updatedAt: "4 days ago" },
    ],
  },

  activity: {
    "crl-214-2024": [
      { type: "ai", text: "AI generated case summary", time: "2h ago" },
      { type: "chat", text: "AI Assistant chat started — “Find all witness statements…”", time: "5h ago" },
      { type: "upload", text: "Charge_sheet.pdf uploaded", time: "1d ago" },
      { type: "note", text: "Note added — “Cross-examination prep”", time: "1d ago" },
      { type: "hearing", text: "Hearing scheduled for 12 Aug 2026", time: "3d ago" },
      { type: "case", text: "Case created", time: "20 Mar 2024" },
    ],
  },

  hearings: [
    { id: "h1", caseId: "civ-89-2023", caseTitle: "Mehta Contract Dispute", date: "2026-08-04", time: "2:00 PM", court: "High Court of Delhi", judge: "Hon. Justice K. Nair", status: "confirmed", notes: "Bring amended contract clause comparison." },
    { id: "h2", caseId: "civ-45-2024", caseTitle: "Iyer Property Title", date: "2026-08-08", time: "9:30 AM", court: "District Court, Chennai", judge: "Hon. Justice M. Balan", status: "confirmed", notes: "Awaiting OCR on 1980s land records." },
    { id: "h3", caseId: "crl-77-2022", caseTitle: "Kumar Bail Application", date: "2026-08-11", time: "11:00 AM", court: "Sessions Court, Mumbai", judge: "Hon. Justice S. Deshmukh", status: "confirmed", notes: "Bail arguments — cite prior clean record." },
    { id: "h4", caseId: "crl-214-2024", caseTitle: "State vs. Sharma", date: "2026-08-12", time: "10:30 AM", court: "District Court, Delhi", judge: "Hon. Justice A. Rao", status: "urgent", notes: "Cross-examination of Witness B." },
    { id: "h5", caseId: "arb-12-2025", caseTitle: "Rao Arbitration", date: "2026-08-17", time: "3:30 PM", court: "Arbitration Tribunal, Bengaluru", judge: "Sole Arbitrator P. Iyengar", status: "confirmed", notes: "Final arguments on penalty clause." },
  ],

  searchIndex: [
    { caseId: "crl-214-2024", caseTitle: "State vs. Sharma", doc: "Postmortem_report.pdf", page: 3, snippet: "…injuries are consistent with a sharp-edged instrument, likely a kitchen knife or similar blade…", score: 0.93 },
    { caseId: "crl-214-2024", caseTitle: "State vs. Sharma", doc: "FIR_copy.pdf", page: 2, snippet: "…the complainant alleges the accused produced a knife during the altercation…", score: 0.88 },
    { caseId: "crl-214-2024", caseTitle: "State vs. Sharma", doc: "Witness_02_statement.docx", page: 1, snippet: "…investigators dusted the recovered object for fingerprints near the scene…", score: 0.71 },
    { caseId: "civ-89-2023", caseTitle: "Mehta Contract Dispute", doc: "Contract_v2.docx", page: 4, snippet: "…clause 4.2 was amended to extend the delivery window by 45 days…", score: 0.65 },
    { caseId: "arb-12-2025", caseTitle: "Rao Arbitration", doc: "Possession_letter.pdf", page: 1, snippet: "…possession was delayed beyond the contractually agreed date without written notice…", score: 0.58 },
  ],

  recentAiChats: [
    { case: "State vs. Sharma", query: "Find all witness statements mentioning fingerprints", time: "5h ago" },
    { case: "Mehta Contract Dispute", query: "Compare contract v1 vs v2 clauses", time: "1d ago" },
    { case: "Kumar Bail Application", query: "Summarize this case", time: "3d ago" },
    { case: "Rao Arbitration", query: "Explain the penalty clause terms", time: "5d ago" },
  ],
};
