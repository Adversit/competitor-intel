"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { Plus, Globe, Tag, MoreHorizontal, ExternalLink, Trash2, ScrollText, PlusCircle } from 'lucide-react';
import Link from 'next/link';

export default function Competitors() {
    const [competitors, setCompetitors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [newComp, setNewComp] = useState({ name: '', website: '', category: 'LLM' });

    async function fetchCompetitors() {
        try {
            const res = await api.getCompetitors();
            setCompetitors(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchCompetitors();
    }, []);

    const handleAdd = async (e: any) => {
        e.preventDefault();
        try {
            await api.createCompetitor(newComp);
            setIsAddModalOpen(false);
            setNewComp({ name: '', website: '', category: 'LLM' });
            fetchCompetitors();
        } catch (err) {
            alert("Error adding competitor");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure?")) return;
        try {
            await api.deleteCompetitor(id);
            fetchCompetitors();
        } catch (err) {
            alert("Error deleting");
        }
    };

    if (loading) return <div className="animate-pulse">Loading competitors...</div>;

    return (
        <div className="space-y-8 animate-in">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Competitors</h1>
                    <p className="text-muted-foreground">Manage companies and products you are monitoring.</p>
                </div>
                <button
                    onClick={() => setIsAddModalOpen(true)}
                    className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-xl flex items-center gap-2 font-medium transition-all"
                >
                    <Plus className="w-5 h-5" />
                    Add Competitor
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {competitors.map((comp: any) => (
                    <div key={comp.id} className="group bg-card/40 border border-border rounded-2xl overflow-hidden hover:border-primary/50 transition-all">
                        <div className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 bg-muted rounded-xl flex items-center justify-center text-xl font-bold text-primary">
                                    {comp.name[0]}
                                </div>
                                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={() => handleDelete(comp.id)}
                                        className="p-2 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                                        title="Delete Competitor"
                                        aria-label="Delete Competitor"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>

                            <h3 className="text-xl font-bold mb-1">{comp.name}</h3>
                            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                                <span className="flex items-center gap-1">
                                    <Tag className="w-3.5 h-3.5" />
                                    {comp.category || 'N/A'}
                                </span>
                                {comp.website && (
                                    <a href={comp.website} target="_blank" className="flex items-center gap-1 hover:text-primary transition-colors">
                                        <Globe className="w-3.5 h-3.5" />
                                        Website
                                        <ExternalLink className="w-3 h-3" />
                                    </a>
                                )}
                            </div>

                            <div className="flex flex-wrap gap-2 mb-6">
                                {(comp.tags || []).map((tag: string) => (
                                    <span key={tag} className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-muted text-muted-foreground border border-border/50">
                                        {tag}
                                    </span>
                                ))}
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <Link
                                    href={`/battlecards/${comp.id}`}
                                    className="flex items-center justify-center gap-2 py-2 rounded-xl bg-muted/50 hover:bg-muted text-sm font-semibold transition-colors"
                                >
                                    <ScrollText className="w-4 h-4" />
                                    Battlecard
                                </Link>
                                <Link
                                    href={`/competitors/${comp.id}`}
                                    className="flex items-center justify-center gap-2 py-2 rounded-xl border border-border hover:border-primary/30 text-sm font-semibold transition-colors"
                                >
                                    Details
                                </Link>
                            </div>
                        </div>
                    </div>
                ))}

                {competitors.length === 0 && (
                    <div className="col-span-full py-20 bg-muted/10 rounded-3xl border-2 border-dashed border-border flex flex-col items-center justify-center text-center">
                        <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-4">
                            <PlusCircle className="w-8 h-8 text-muted-foreground" />
                        </div>
                        <h3 className="text-lg font-semibold">No competitors yet</h3>
                        <p className="text-muted-foreground mt-1 max-w-xs">Start by adding your first competitor to monitor their changes.</p>
                        <button
                            onClick={() => setIsAddModalOpen(true)}
                            className="mt-6 text-primary font-bold hover:underline"
                        >
                            Add your first competitor
                        </button>
                    </div>
                )}
            </div>

            {isAddModalOpen && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-card border border-border w-full max-w-md rounded-3xl p-8 animate-in shadow-2xl">
                        <h2 className="text-2xl font-bold mb-6">Add Competitor</h2>
                        <form onSubmit={handleAdd} className="space-y-5">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Name</label>
                                <input
                                    required
                                    value={newComp.name}
                                    onChange={e => setNewComp({ ...newComp, name: e.target.value })}
                                    className="w-full bg-muted border border-border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium"
                                    placeholder="e.g. OpenAI"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Website URL</label>
                                <input
                                    value={newComp.website}
                                    onChange={e => setNewComp({ ...newComp, website: e.target.value })}
                                    className="w-full bg-muted border border-border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium"
                                    placeholder="https://..."
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Category</label>
                                <select
                                    value={newComp.category}
                                    onChange={e => setNewComp({ ...newComp, category: e.target.value })}
                                    className="w-full bg-muted border border-border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium appearance-none"
                                    aria-label="Category"
                                    title="Category"
                                >
                                    {['LLM', 'Agent', 'Tool', 'Platform', 'Other'].map(c => (
                                        <option key={c} value={c}>{c}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsAddModalOpen(false)}
                                    className="flex-1 px-4 py-3 rounded-xl border border-border font-bold hover:bg-muted transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 bg-primary text-white px-4 py-3 rounded-xl font-bold hover:bg-primary/90 transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)]"
                                >
                                    Create
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
