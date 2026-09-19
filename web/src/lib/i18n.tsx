/* Tiny UI localisation: a dictionary per language and a `t()` hook.
   Strings missing from a language fall back to English, so adding a language
   never breaks the page. Email content is translated separately by the API. */
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export const LANGS = [
  ["en", "English"], ["ms", "Bahasa Melayu"], ["zh", "中文"],
] as const;
export type Lang = (typeof LANGS)[number][0];

const en = {
  // navigation and shell
  "nav.inbox": "Inbox", "nav.invoices": "Invoices", "nav.impact": "Impact", "nav.help": "Help",
  "nav.language": "Language", "nav.settings": "Settings: API server address",
  "nav.theme.light": "Switch to light theme", "nav.theme.dark": "Switch to dark theme", "nav.skip": "Skip to main content",
  "footer.line": "Student prototype by team {team} for the {event}. Not an Averis product.",
  "footer.contact": "Contact", "footer.privacy": "Privacy", "footer.terms": "Terms", "footer.cookies": "Cookies", "footer.accessibility": "Accessibility",
  // inbox
  "inbox.title": "Inbox", "inbox.subtitle": "Every email triaged; document checks flagged for review.",
  "inbox.process": "Process inbox", "inbox.processing": "Processing…",
  "tile.emails": "Emails", "tile.mismatch": "Mismatches to amend", "tile.review": "Need human review", "tile.clean": "Checked clean",
  "tile.showing": "Showing these", "tile.click": "Click to show",
  "filter.search": "Search", "filter.search.ph": "Subject, sender or id", "filter.category": "Category", "filter.status": "Status",
  "filter.source": "Source", "filter.sort": "Sort by", "filter.clear": "Clear",
  "filter.all.categories": "All categories", "filter.all.statuses": "All statuses", "filter.all.sources": "All sources",
  "sort.newest": "Newest first", "sort.oldest": "Oldest first", "sort.severity": "Most urgent first", "sort.category": "Category", "sort.sender": "Sender A to Z", "sort.subject": "Subject A to Z",
  "source.dataset": "Hackathon dataset", "source.mailbox": "Connected mailbox", "source.upload": "Uploaded .eml",
  "inbox.showing": "Showing {n} of {total} emails", "inbox.none": "No emails match these filters.", "inbox.clearFilters": "Clear filters",
  "inbox.noResults": "No results yet. Choose Process inbox to run the pipeline.",
  "inbox.apiError": "Could not reach the API: {err}. Is sdoc serve running? Check the address under the gear icon.",
  "col.email": "Email", "col.from": "From", "col.category": "Category", "col.status": "Status", "col.fields": "Fields", "col.attachments": "attachments",
  // categories and statuses
  "cat.BL_COMPARISON": "BL comparison", "cat.SI_REQUEST": "SI request", "cat.INVOICE_QUERY": "Invoice query", "cat.GENERAL": "General", "cat.SPAM": "Spam",
  "status.OK": "OK", "status.MISMATCH": "Mismatch", "status.NEEDS_REVIEW": "Needs review",
  // mail sources
  "sources.title": "Email sources", "sources.default": "Hackathon dataset loaded. Connect a real mailbox or upload an email.",
  "sources.connected": "Connected to {user} ({host}, {folder}).",
  "sources.connect": "Connect mailbox", "sources.fetch": "Fetch new mail", "sources.disconnect": "Disconnect", "sources.upload": "Upload .eml",
  // compare
  "compare.back": "Back to inbox", "compare.approve": "Approve result", "compare.override": "Override result", "compare.copy": "Copy draft reply",
  "compare.email": "Email", "compare.table": "Shipping Instruction vs draft Bill of Lading", "compare.draft": "Drafted reply (a person sends it)",
  "compare.translateTo": "Translate to", "compare.translate": "Translate", "compare.translating": "Translating…",
  "compare.field": "Field", "compare.si": "SI", "compare.bl": "Draft BL", "compare.result": "Result",
  "compare.match": "Match", "compare.mismatch": "Mismatch", "compare.missing": "Missing", "compare.hover": "Hover or focus a value to see the source line it was read from.",
  // other pages
  "invoices.title": "Invoices and receipts", "impact.title": "Impact", "help.title": "How to get your inbox in",
};
export type Key = keyof typeof en;

const ms: Partial<Record<Key, string>> = {
  "nav.inbox": "Peti masuk", "nav.invoices": "Invois", "nav.impact": "Impak", "nav.help": "Bantuan", "nav.language": "Bahasa",
  "nav.settings": "Tetapan: alamat pelayan API", "nav.theme.light": "Tukar ke tema cerah", "nav.theme.dark": "Tukar ke tema gelap", "nav.skip": "Langkau ke kandungan utama",
  "footer.line": "Prototaip pelajar oleh pasukan {team} untuk {event}. Bukan produk Averis.",
  "footer.contact": "Hubungi", "footer.privacy": "Privasi", "footer.terms": "Terma", "footer.cookies": "Kuki", "footer.accessibility": "Kebolehcapaian",
  "inbox.title": "Peti masuk", "inbox.subtitle": "Setiap e-mel disusun; semakan dokumen ditanda untuk semakan.",
  "inbox.process": "Proses peti masuk", "inbox.processing": "Memproses…",
  "tile.emails": "E-mel", "tile.mismatch": "Ketidakpadanan untuk dipinda", "tile.review": "Perlu semakan manusia", "tile.clean": "Disemak bersih",
  "tile.showing": "Sedang dipaparkan", "tile.click": "Klik untuk papar",
  "filter.search": "Cari", "filter.search.ph": "Subjek, penghantar atau id", "filter.category": "Kategori", "filter.status": "Status",
  "filter.source": "Sumber", "filter.sort": "Susun ikut", "filter.clear": "Kosongkan",
  "filter.all.categories": "Semua kategori", "filter.all.statuses": "Semua status", "filter.all.sources": "Semua sumber",
  "sort.newest": "Terbaru dahulu", "sort.oldest": "Terlama dahulu", "sort.severity": "Paling mendesak dahulu", "sort.category": "Kategori", "sort.sender": "Penghantar A ke Z", "sort.subject": "Subjek A ke Z",
  "source.dataset": "Set data hackathon", "source.mailbox": "Peti mel disambung", "source.upload": ".eml dimuat naik",
  "inbox.showing": "Memaparkan {n} daripada {total} e-mel", "inbox.none": "Tiada e-mel sepadan dengan penapis ini.", "inbox.clearFilters": "Kosongkan penapis",
  "inbox.noResults": "Belum ada keputusan. Pilih Proses peti masuk untuk menjalankan saluran.",
  "inbox.apiError": "Tidak dapat mencapai API: {err}. Adakah sdoc serve berjalan? Semak alamat di bawah ikon gear.",
  "col.email": "E-mel", "col.from": "Daripada", "col.category": "Kategori", "col.status": "Status", "col.fields": "Medan", "col.attachments": "lampiran",
  "cat.BL_COMPARISON": "Perbandingan BL", "cat.SI_REQUEST": "Permintaan SI", "cat.INVOICE_QUERY": "Pertanyaan invois", "cat.GENERAL": "Umum", "cat.SPAM": "Spam",
  "status.OK": "OK", "status.MISMATCH": "Tidak padan", "status.NEEDS_REVIEW": "Perlu semakan",
  "sources.title": "Sumber e-mel", "sources.default": "Set data hackathon dimuatkan. Sambungkan peti mel sebenar atau muat naik e-mel.",
  "sources.connected": "Disambung ke {user} ({host}, {folder}).",
  "sources.connect": "Sambung peti mel", "sources.fetch": "Ambil mel baharu", "sources.disconnect": "Putuskan", "sources.upload": "Muat naik .eml",
  "compare.back": "Kembali ke peti masuk", "compare.approve": "Luluskan keputusan", "compare.override": "Ganti keputusan", "compare.copy": "Salin draf balasan",
  "compare.email": "E-mel", "compare.table": "Arahan Penghantaran vs draf Bil Muatan", "compare.draft": "Draf balasan (dihantar oleh manusia)",
  "compare.translateTo": "Terjemah ke", "compare.translate": "Terjemah", "compare.translating": "Menterjemah…",
  "compare.field": "Medan", "compare.si": "SI", "compare.bl": "Draf BL", "compare.result": "Keputusan",
  "compare.match": "Padan", "compare.mismatch": "Tidak padan", "compare.missing": "Tiada", "compare.hover": "Tuding atau fokus pada nilai untuk melihat baris sumbernya.",
  "invoices.title": "Invois dan resit", "impact.title": "Impak", "help.title": "Cara memasukkan peti masuk anda",
};

const zh: Partial<Record<Key, string>> = {
  "nav.inbox": "收件箱", "nav.invoices": "发票", "nav.impact": "成效", "nav.help": "帮助", "nav.language": "语言",
  "nav.settings": "设置：API 服务器地址", "nav.theme.light": "切换到浅色主题", "nav.theme.dark": "切换到深色主题", "nav.skip": "跳到主要内容",
  "footer.line": "由 {team} 团队为 {event} 制作的学生原型。并非 Averis 产品。",
  "footer.contact": "联系", "footer.privacy": "隐私", "footer.terms": "条款", "footer.cookies": "Cookie", "footer.accessibility": "无障碍",
  "inbox.title": "收件箱", "inbox.subtitle": "每封邮件已分类；单据核对已标记待审。",
  "inbox.process": "处理收件箱", "inbox.processing": "处理中…",
  "tile.emails": "邮件", "tile.mismatch": "需修改的不符项", "tile.review": "需人工审核", "tile.clean": "核对无误",
  "tile.showing": "当前显示", "tile.click": "点击查看",
  "filter.search": "搜索", "filter.search.ph": "主题、发件人或编号", "filter.category": "类别", "filter.status": "状态",
  "filter.source": "来源", "filter.sort": "排序", "filter.clear": "清除",
  "filter.all.categories": "所有类别", "filter.all.statuses": "所有状态", "filter.all.sources": "所有来源",
  "sort.newest": "最新优先", "sort.oldest": "最早优先", "sort.severity": "最紧急优先", "sort.category": "类别", "sort.sender": "发件人 A 到 Z", "sort.subject": "主题 A 到 Z",
  "source.dataset": "黑客松数据集", "source.mailbox": "已连接邮箱", "source.upload": "上传的 .eml",
  "inbox.showing": "显示 {n} / {total} 封邮件", "inbox.none": "没有符合筛选条件的邮件。", "inbox.clearFilters": "清除筛选",
  "inbox.noResults": "尚无结果。点击“处理收件箱”运行流程。",
  "inbox.apiError": "无法连接 API：{err}。sdoc serve 在运行吗？请检查齿轮图标下的地址。",
  "col.email": "邮件", "col.from": "发件人", "col.category": "类别", "col.status": "状态", "col.fields": "字段", "col.attachments": "个附件",
  "cat.BL_COMPARISON": "提单核对", "cat.SI_REQUEST": "SI 请求", "cat.INVOICE_QUERY": "发票查询", "cat.GENERAL": "一般", "cat.SPAM": "垃圾邮件",
  "status.OK": "无误", "status.MISMATCH": "不符", "status.NEEDS_REVIEW": "需审核",
  "sources.title": "邮件来源", "sources.default": "已加载黑客松数据集。可连接真实邮箱或上传邮件。",
  "sources.connected": "已连接 {user}（{host}，{folder}）。",
  "sources.connect": "连接邮箱", "sources.fetch": "获取新邮件", "sources.disconnect": "断开", "sources.upload": "上传 .eml",
  "compare.back": "返回收件箱", "compare.approve": "批准结果", "compare.override": "覆盖结果", "compare.copy": "复制回复草稿",
  "compare.email": "邮件", "compare.table": "装运指示 与 提单草稿", "compare.draft": "回复草稿（由人工发送）",
  "compare.translateTo": "翻译为", "compare.translate": "翻译", "compare.translating": "翻译中…",
  "compare.field": "字段", "compare.si": "SI", "compare.bl": "提单草稿", "compare.result": "结果",
  "compare.match": "一致", "compare.mismatch": "不符", "compare.missing": "缺失", "compare.hover": "悬停或聚焦某个值以查看其来源行。",
  "invoices.title": "发票与收据", "impact.title": "成效", "help.title": "如何接入你的收件箱",
};

const DICT: Record<Lang, Partial<Record<Key, string>>> = { en, ms, zh };

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (k: Key, vars?: Record<string, string | number>) => string };
const I18nContext = createContext<Ctx>({ lang: "en", setLang: () => undefined, t: (k) => en[k] });

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    try { const s = localStorage.getItem("sdoc.uiLang") as Lang | null; if (s && DICT[s]) return s; } catch { /* ignore */ }
    const nav = navigator.language.slice(0, 2) as Lang;
    return DICT[nav] ? nav : "en";
  });
  useEffect(() => { document.documentElement.lang = lang; try { localStorage.setItem("sdoc.uiLang", lang); } catch { /* ignore */ } }, [lang]);
  const value = useMemo<Ctx>(() => ({
    lang,
    setLang: setLangState,
    t: (k, vars) => {
      let s = DICT[lang][k] ?? en[k] ?? k;
      for (const [name, v] of Object.entries(vars ?? {})) s = s.replace(`{${name}}`, String(v));
      return s;
    },
  }), [lang]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export const useT = () => useContext(I18nContext);
