"use client";

import React, { useEffect, useRef, useState } from "react";
import { AlertTriangle, PhoneCall, Send, Sparkles, Trash2, X } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  emergency?: boolean;
  confidence?: number;
  sources?: string[];
  suggestions?: string[];
}

interface HealthBuddyChatProps {
  lang: "en" | "hi";
  assessmentContext: Record<string, string>;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DEFAULT_PROMPTS_EN = [
  "Explain my risk results",
  "What foods should I eat and avoid?",
  "What exercises are safe for me?",
  "Which verified hospitals fit my plan?",
  "How accurate are HealthBuddy's ML models?",
];

const DEFAULT_PROMPTS_HI = [
  "मेरे जोखिम परिणाम समझाएं",
  "मुझे क्या खाना चाहिए और क्या टालना चाहिए?",
  "मेरे लिए सुरक्षित व्यायाम क्या हैं?",
  "मुझे किस डॉक्टर से मिलना चाहिए?",
];

export function HealthBuddyChat({
  lang,
  assessmentContext,
  open,
  onOpenChange,
}: HealthBuddyChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text:
        lang === "hi"
          ? "नमस्ते! मैं **HealthBuddy** हूँ — आपका ML-प्रशिक्षित स्वास्थ्य ज्ञान सहायक। अपने जोखिम स्कोर, भारतीय आहार, व्यायाम या सत्यापित अस्पतालों के बारे में पूछें।"
          : "Hi! I'm **HealthBuddy**, your ML-trained clinical knowledgebase assistant. Ask me about your risk results, Indian diet guidance, safe exercises, ML model accuracy, or verified hospitals.",
      suggestions: lang === "hi" ? DEFAULT_PROMPTS_HI : DEFAULT_PROMPTS_EN,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docCount, setDocCount] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const dialogRef = useRef<HTMLElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    apiFetch<{ doc_count: number }>("/api/v1/chat/status")
      .then((res) => {
        if (typeof res?.doc_count === "number") setDocCount(res.doc_count);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  // Esc to close + basic focus management & trap inside dialog
  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onOpenChange(false);
        return;
      }
      if (e.key === "Tab" && dialogRef.current) {
        const focusables = dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'
        );
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: ChatMessage = {
      id: `u_${Date.now()}`,
      role: "user",
      text: trimmed,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await apiFetch<{
        reply: string;
        emergency: boolean;
        confidence: number;
        sources: string[];
        suggestions: string[];
      }>("/api/v1/chat", {
        method: "POST",
        body: JSON.stringify({
          message: trimmed,
          lang,
          assessment_context: assessmentContext,
        }),
      });

      setMessages((prev) => [
        ...prev,
        {
          id: `a_${Date.now()}`,
          role: "assistant",
          text: res.reply,
          emergency: res.emergency,
          confidence: res.confidence,
          sources: res.sources || [],
          suggestions: res.suggestions || [],
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: "assistant",
          text: "Unable to reach the HealthBuddy backend right now. Please verify the API server is running.",
          suggestions: DEFAULT_PROMPTS_EN,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function resetChat() {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        text:
          lang === "hi"
            ? "नमस्ते! मैं **HealthBuddy** हूँ। अपने स्वास्थ्य परिणामों या योजना के बारे में पूछें।"
            : "Hi! I'm **HealthBuddy**. Ask me anything about your screening results, diet, exercise, or verified care options.",
        suggestions: lang === "hi" ? DEFAULT_PROMPTS_HI : DEFAULT_PROMPTS_EN,
      },
    ]);
  }

  function renderFormattedText(raw: string) {
    return raw.split("\n").map((line, idx) => {
      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <p key={idx} className={idx > 0 ? "mt-1.5" : ""}>
          {parts.map((part, i) =>
            part.startsWith("**") && part.endsWith("**") ? (
              <strong key={i} className="font-bold">
                {part.slice(2, -2)}
              </strong>
            ) : (
              <React.Fragment key={i}>{part}</React.Fragment>
            )
          )}
        </p>
      );
    });
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={() => onOpenChange(true)}
          aria-label="Open HealthBuddy AI Chat"
          data-no-print="true"
          className="fixed bottom-20 lg:bottom-5 right-5 z-40 min-h-[48px] px-4 py-2.5 rounded-full bg-hb-cta hover:bg-hb-accent text-hb-ctaInk border border-hb-border shadow-md inline-flex items-center gap-2.5 text-xs font-extrabold transition-transform duration-150 hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-hb-accent focus:ring-offset-2"
        >
          <span className="w-7 h-7 rounded-full bg-hb-surface flex items-center justify-center p-1 border border-hb-border">
            <img src="/healthbuddy-logo.svg" alt="" className="w-full h-full" aria-hidden="true" />
          </span>
          <span>Ask HealthBuddy</span>
          <span className="px-1.5 py-0.5 rounded-full bg-hb-ink text-hb-surface text-[10px] font-bold">
            ML
          </span>
        </button>
      )}

      {open && (
        <section
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-label="HealthBuddy ML Assistant"
          data-no-print="true"
          className="fixed bottom-4 right-4 z-50 w-[calc(100vw-2rem)] sm:w-[410px] h-[560px] max-h-[82vh] rounded-lg bg-hb-canvas border border-hb-border shadow-md flex flex-col overflow-hidden"
        >
          <div className="bg-hb-surface px-4 py-3 border-b border-hb-border flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-md bg-hb-accentSoft p-1.5 border border-hb-border flex items-center justify-center">
                <img src="/healthbuddy-logo.svg" alt="HealthBuddy logo" className="w-full h-full" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-sm text-hb-ink">HealthBuddy</span>
                  <span className="px-1.5 py-0.5 rounded-full bg-hb-accentSoft text-hb-accentInk text-[10px] font-bold uppercase">
                    ML KB
                  </span>
                </div>
                <p className="text-[11px] text-hb-muted tabular-nums">
                  {docCount ? `${docCount} clinical docs indexed` : "Clinical knowledgebase assistant"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={resetChat}
                aria-label="Clear chat"
                className="w-9 h-9 rounded-md hover:bg-hb-subtle text-hb-muted hover:text-hb-ink flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-hb-accent"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                aria-label="Close HealthBuddy chat"
                className="w-9 h-9 rounded-md hover:bg-hb-subtle text-hb-muted hover:text-hb-ink flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-hb-accent"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[88%] rounded-lg px-3.5 py-2.5 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-hb-cta text-hb-ctaInk font-semibold shadow-sm"
                      : m.emergency
                      ? "bg-hb-highBg border border-hb-highBorder text-hb-highInk font-semibold"
                      : "bg-hb-surface border border-hb-border text-hb-ink shadow-sm"
                  }`}
                >
                  {m.emergency && (
                    <div className="flex items-center gap-1.5 text-xs font-extrabold uppercase mb-1.5 text-hb-highInk">
                      <AlertTriangle className="w-4 h-4" aria-hidden="true" />
                      <span>Emergency Red-Flag Override</span>
                    </div>
                  )}
                  <div>{renderFormattedText(m.text)}</div>

                  {m.emergency && (
                    <div className="mt-2.5 flex flex-wrap gap-2">
                      <a
                        href="tel:112"
                        className="px-3 py-1.5 rounded-md bg-hb-highInk text-white text-xs font-bold inline-flex items-center gap-1.5"
                      >
                        <PhoneCall className="w-3.5 h-3.5" aria-hidden="true" />
                        <span>Call 112</span>
                      </a>
                      <a
                        href="tel:108"
                        className="px-3 py-1.5 rounded-md bg-hb-surface border border-hb-highBorder text-hb-highInk text-xs font-bold inline-flex items-center gap-1.5"
                      >
                        <PhoneCall className="w-3.5 h-3.5" aria-hidden="true" />
                        <span>Call 108</span>
                      </a>
                    </div>
                  )}

                  {m.role === "assistant" &&
                  (m.sources?.length || (typeof m.confidence === "number" && m.confidence > 0)) ? (
                    <div className="mt-2 pt-2 border-t border-hb-border flex flex-wrap items-center justify-between gap-1.5 text-[11px] text-hb-muted">
                      <span className="truncate max-w-[220px]">
                        {m.sources && m.sources.length > 0 ? `Source: ${m.sources[0]}` : ""}
                      </span>
                      {typeof m.confidence === "number" && m.confidence > 0 && (
                        <span className="px-1.5 py-0.5 rounded-full bg-hb-subtle border border-hb-border font-semibold text-hb-ink tabular-nums">
                          ML match {(m.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  ) : null}
                </div>

                {m.role === "assistant" && m.suggestions && m.suggestions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2 max-w-[95%]">
                    {m.suggestions.slice(0, 3).map((sug) => (
                      <button
                        key={sug}
                        type="button"
                        onClick={() => sendMessage(sug)}
                        disabled={loading}
                        className="px-2.5 py-1 rounded-full bg-hb-surface hover:bg-hb-subtle border border-hb-border text-xs font-semibold text-hb-ink inline-flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors"
                      >
                        <Sparkles className="w-3 h-3 text-hb-accent" aria-hidden="true" />
                        <span>{sug}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-start">
                <div className="rounded-lg bg-hb-surface border border-hb-border px-3.5 py-2.5 text-xs font-semibold text-hb-muted animate-pulse">
                  HealthBuddy is searching clinical knowledgebase...
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage(input);
            }}
            className="p-3 bg-hb-surface border-t border-hb-border space-y-1.5"
          >
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={lang === "hi" ? "HealthBuddy से पूछें..." : "Ask HealthBuddy anything..."}
                aria-label="Ask HealthBuddy"
                className="flex-1 min-h-[44px] px-3.5 py-2 rounded-md bg-hb-canvas border border-hb-border text-sm text-hb-ink placeholder:text-hb-muted focus:outline-none focus:ring-2 focus:ring-hb-accent"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                aria-label="Send message"
                className="min-h-[44px] px-3.5 rounded-md bg-hb-cta hover:bg-hb-accent text-hb-ctaInk font-extrabold inline-flex items-center justify-center disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[11px] text-hb-muted text-center">
              Educational guidance only — not a medical diagnosis.
            </p>
          </form>
        </section>
      )}
    </>
  );
}
