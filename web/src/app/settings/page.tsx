"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';
import { Save, Lock, Server, Cpu } from 'lucide-react';

export default function Settings() {
    const [settings, setSettings] = useState<any>({
        provider: 'openai',
        model: 'gpt-4',
        api_key_masked: '',
        api_base_url: '',
        temperature: 0.3
    });
    const [apiKeyInput, setApiKeyInput] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        async function fetchSettings() {
            try {
                const res = await api.getSettings();
                setSettings(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        fetchSettings();
    }, []);

    const handleSave = async (e: any) => {
        e.preventDefault();
        setSaving(true);
        try {
            const payload = {
                provider: settings.provider,
                model: settings.model,
                api_base_url: settings.api_base_url,
                temperature: settings.temperature,
                // Only send API key if user typed something new
                api_key: apiKeyInput || undefined
            };

            await api.updateSettings(payload);
            alert("Settings saved successfully!");
            // clear sensitive input
            setApiKeyInput('');
            const res = await api.getSettings();
            setSettings(res.data);
        } catch (err) {
            alert("Failed to save settings");
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="p-8">Loading settings...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-in">
            <div>
                <h1 className="text-3xl font-bold tracking-tight mb-2">System Settings</h1>
                <p className="text-muted-foreground">Configure AI providers and system parameters.</p>
            </div>

            <form onSubmit={handleSave} className="space-y-6">
                <div className="bg-card/30 border border-border rounded-3xl p-8 shadow-sm">
                    <div className="flex items-center gap-2 mb-6 text-xl font-bold">
                        <Cpu className="text-primary" />
                        <h2>LLM Configuration</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-muted-foreground">Provider</label>
                            <select
                                value={settings.provider}
                                onChange={e => setSettings({ ...settings, provider: e.target.value })}
                                className="w-full bg-muted border border-border rounded-xl px-4 py-3 appearance-none font-medium focus:ring-2 focus:ring-primary/50 outline-none"
                                aria-label="LLM Provider"
                                title="LLM Provider"
                            >
                                <option value="openai">OpenAI Compatible (ChatGPT, Qwen, DeepSeek)</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-muted-foreground">Model Name</label>
                            <input
                                value={settings.model}
                                onChange={e => setSettings({ ...settings, model: e.target.value })}
                                className="w-full bg-muted border border-border rounded-xl px-4 py-3 font-medium focus:ring-2 focus:ring-primary/50 outline-none"
                                placeholder="e.g. gpt-4o, qwen-plus"
                            />
                            <p className="text-xs text-muted-foreground ml-1">
                                Recommend: <code>gpt-4o</code>, <code>qwen-plus</code>, <code>qwen-max</code>
                            </p>
                        </div>

                        <div className="col-span-full space-y-2">
                            <label className="text-sm font-medium text-muted-foreground">API Key</label>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <input
                                    type="password"
                                    value={apiKeyInput}
                                    onChange={e => setApiKeyInput(e.target.value)}
                                    className="w-full bg-muted border border-border rounded-xl pl-10 pr-4 py-3 font-medium focus:ring-2 focus:ring-primary/50 outline-none"
                                    placeholder={settings.is_configured ? "******** (Leave empty to keep current)" : "Enter API Key"}
                                />
                            </div>
                            {settings.is_configured && !apiKeyInput && (
                                <p className="text-xs text-green-500 font-medium ml-1 flex items-center gap-1">
                                    ✓ API Key is currently configured
                                </p>
                            )}
                        </div>

                        <div className="col-span-full space-y-2">
                            <label className="text-sm font-medium text-muted-foreground">API Base URL (Optional)</label>
                            <div className="relative">
                                <Server className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <input
                                    value={settings.api_base_url || ''}
                                    onChange={e => setSettings({ ...settings, api_base_url: e.target.value })}
                                    className="w-full bg-muted border border-border rounded-xl pl-10 pr-4 py-3 font-medium focus:ring-2 focus:ring-primary/50 outline-none"
                                    placeholder="https://api.openai.com/v1"
                                />
                            </div>
                            <div className="text-xs text-muted-foreground ml-1 space-y-1 p-2 bg-muted/50 rounded-lg border border-border/50">
                                <p>Common Endpoints:</p>
                                <ul className="list-disc pl-4 space-y-0.5">
                                    <li><strong>Qwen (Tongyi):</strong> <code>https://dashscope.aliyuncs.com/compatible-mode/v1</code></li>
                                    <li><strong>DeepSeek:</strong> <code>https://api.deepseek.com</code></li>
                                    <li><strong>OpenAI:</strong> (Leave empty)</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={saving}
                        className="bg-primary text-white font-bold px-8 py-3 rounded-xl hover:bg-primary/90 transition-all flex items-center gap-2 shadow-lg shadow-primary/25 disabled:opacity-50"
                    >
                        {saving ? 'Saving...' : (
                            <>
                                <Save className="w-5 h-5" />
                                Save Configuration
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}
