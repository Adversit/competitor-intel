"use client";

import { useEffect, useState, use } from 'react';
import { api } from '@/lib/api/client';
import { formatDate } from '@/lib/utils';
import { ChevronLeft, Wand2, Download, Share2, History } from 'lucide-react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';

export default function BattlecardDetail({ params: paramsPromise }: { params: Promise<{ id: string }> }) {
    const params = use(paramsPromise);
    const [battlecard, setBattlecard] = useState<any>(null);
    const [competitor, setCompetitor] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    async function fetchData() {
        setLoading(true);
        setError(null);
        try {
            const [bcRes, compRes] = await Promise.all([
                api.getBattlecard(params.id),
                api.getCompetitor(params.id)
            ]);
            setBattlecard(bcRes.data);
            setCompetitor(compRes.data);
        } catch (err: any) {
            if (err.response?.status === 404) {
                setError("BATTLECARD_NOT_FOUND");
                // Still need competitor info to show the name
                try {
                    const compRes = await api.getCompetitor(params.id);
                    setCompetitor(compRes.data);
                } catch (e) { }
            } else {
                setError("Failed to load data");
            }
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchData();
    }, [params.id]);

    const handleGenerate = async () => {
        try {
            setLoading(true);
            await api.generateBattlecard(params.id);
            await fetchData();
        } catch (err) {
            alert("AI Generation failed. Check backend logs and LLM config.");
            setLoading(false);
        }
    };


    if (loading && !battlecard) return <div className="p-8">Loading battlecard...</div>;

    const handleDownload = () => {
        if (!battlecard) return;
        const blob = new Blob([battlecard.content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${competitor.name.replace(/\s+/g, '_')}-battlecard.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="space-y-8 animate-in pb-20">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <Link href="/battlecards" className="p-2 rounded-xl hover:bg-muted transition-colors">
                        <ChevronLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">{competitor?.name || 'Loading...'} Battlecard</h1>
                        {battlecard && (
                            <p className="text-muted-foreground text-sm">
                                Version {battlecard.version} • Last updated {formatDate(battlecard.updated_at)}
                            </p>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2 no-print">
                    <button
                        onClick={handleGenerate}
                        disabled={loading}
                        className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-xl font-bold text-sm hover:bg-primary/90 transition-all disabled:opacity-50"
                    >
                        <Wand2 className="w-4 h-4" />
                        {loading ? 'Thinking...' : 'Regenerate with AI'}
                    </button>

                    <button
                        onClick={handleDownload}
                        className="p-2 rounded-xl border border-border hover:bg-muted text-muted-foreground transition-colors"
                        title="Download Markdown"
                    >
                        <Download className="w-4 h-4" />
                    </button>

                    <button
                        onClick={() => window.print()}
                        className="p-2 rounded-xl border border-border hover:bg-muted text-muted-foreground transition-colors"
                        title="Print / Save as PDF"
                    >
                        <Share2 className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {error === "BATTLECARD_NOT_FOUND" ? (
                <div className="py-20 text-center bg-card/20 border border-dashed border-border rounded-3xl">
                    <History className="w-12 h-12 mx-auto mb-4 opacity-20" />
                    <h3 className="text-xl font-bold">No Battlecard for {competitor?.name}</h3>
                    <p className="text-muted-foreground mt-2">AI needs to analyze existing snapshots to generate a comparison card.</p>
                    <button
                        onClick={handleGenerate}
                        className="mt-6 bg-primary/10 text-primary px-6 py-3 rounded-2xl font-bold hover:bg-primary/20 transition-all flex items-center gap-2 mx-auto"
                    >
                        <Wand2 className="w-5 h-5" />
                        Generate Initial Card
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                    <div className="lg:col-span-3">
                        <div className="bg-card/30 border border-border rounded-3xl p-8 md:p-12 prose prose-invert prose-blue max-w-none shadow-2xl">
                            {battlecard ? (
                                <article className="markdown-content">
                                    <ReactMarkdown>{battlecard.content}</ReactMarkdown>
                                </article>
                            ) : (
                                <div className="animate-pulse space-y-4">
                                    <div className="h-8 bg-muted rounded w-1/4"></div>
                                    <div className="h-4 bg-muted rounded w-full"></div>
                                    <div className="h-4 bg-muted rounded w-full"></div>
                                    <div className="h-4 bg-muted rounded w-3/4"></div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="space-y-6 no-print">
                        <div className="bg-card/20 border border-border rounded-2xl p-6">
                            <h3 className="font-bold mb-4 flex items-center gap-2">
                                <Share2 className="w-4 h-4 text-primary" />
                                Actions
                            </h3>
                            <div className="space-y-3">
                                <button onClick={() => window.print()} className="w-full text-left px-4 py-3 rounded-xl border border-border hover:bg-muted text-sm font-medium transition-colors">Export as PDF</button>
                                <button className="w-full text-left px-4 py-3 rounded-xl border border-border hover:bg-muted text-sm font-medium transition-colors">Share link</button>
                            </div>
                        </div>

                        <div className="bg-card/20 border border-border rounded-2xl p-6">
                            <h3 className="font-bold mb-4 flex items-center gap-2">
                                <History className="w-4 h-4 text-primary" />
                                Quick Stats
                            </h3>
                            <div className="space-y-4 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Category</span>
                                    <span className="font-medium">{competitor?.category || 'N/A'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Sources</span>
                                    <span className="font-medium">{(competitor?.sources?.length) || 0}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <style jsx global>{`
        @media print {
          nav, button, .no-print { display: none !important; }
          body { background: white; color: black; }
          .markdown-content { font-size: 12pt; }
        }
        .markdown-content h1 { font-size: 2.25rem; font-weight: 800; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
        .markdown-content h2 { font-size: 1.5rem; font-weight: 700; margin-top: 2.5rem; margin-bottom: 1.25rem; color: var(--primary); }
        .markdown-content h3 { font-size: 1.25rem; font-weight: 600; margin-top: 1.5rem; }
        .markdown-content p { color: var(--muted-foreground); line-height: 1.75; margin-bottom: 1.25rem; }
        .markdown-content ul { list-style-type: disc; padding-left: 1.5rem; margin-bottom: 1.25rem; }
        .markdown-content li { margin-bottom: 0.5rem; color: var(--muted-foreground); }
        .markdown-content table { width: 100%; border-collapse: collapse; margin: 2rem 0; font-size: 0.875rem; }
        .markdown-content th { background: var(--muted); padding: 0.75rem 1rem; text-align: left; font-weight: 600; border: 1px solid var(--border); }
        .markdown-content td { padding: 0.75rem 1rem; border: 1px solid var(--border); }
        .markdown-content blockquote { border-left: 4px solid var(--primary); padding-left: 1.5rem; font-style: italic; margin: 1.5rem 0; }
      `}</style>
        </div>
    );
}
