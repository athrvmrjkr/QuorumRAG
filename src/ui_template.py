# Quorum Moon Chat UI Template with Spline 3D Scene Background
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>Quorum AI — Multi-Agent Research Assistant</title>
    <!-- Modern SVG Favicon matching Quorum Quantum Orbital Emblem -->
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='2' y1='2' x2='30' y2='30' gradientUnits='userSpaceOnUse'%3E%3Cstop offset='0%25' stop-color='%2338bdf8'/%3E%3Cstop offset='50%25' stop-color='%23818cf8'/%3E%3Cstop offset='100%25' stop-color='%23c084fc'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='32' height='32' rx='8' fill='%2308090c'/%3E%3Ccircle cx='16' cy='16' r='11' stroke='url(%23g)' stroke-width='2' stroke-dasharray='22 6' fill='none'/%3E%3Ccircle cx='16' cy='16' r='6.5' stroke='%2338bdf8' stroke-width='1.5' stroke-dasharray='10 6' fill='none' opacity='0.75'/%3E%3Ccircle cx='16' cy='16' r='2.8' fill='%23ffffff'/%3E%3C/svg%3E">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    
    <!-- Marked.js for Rich Markdown & Table Rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked@13.0.2/marked.min.js"></script>

    <!-- MathJax 3 for Universal LaTeX Math Rendering -->
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
            }
        };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

    <style>
        :root {
            --bg-base: #060709;
            --card-glass: rgba(10, 11, 15, 0.72);
            --border-glass: rgba(255, 255, 255, 0.14);
            --border-hover: rgba(255, 255, 255, 0.3);
            --text-main: #ffffff;
            --text-muted: #9ca3af;
            --text-sub: #d1d5db;
            --accent: #ffffff;
            --green: #22c55e;
            --yellow: #eab308;
            --red: #ef4444;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body, html {
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: var(--bg-base);
            color: var(--text-main);
        }

        /* 3D Spline Canvas and Ambient Background */
        #canvas3d {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 0;
            pointer-events: auto;
        }

        /* Completely suppress & obliterate 'Built with Spline' badge */
        #spline-logo,
        .spline-watermark,
        a[href*="spline.design"],
        a[href*="spline.com"],
        #canvas3d + a,
        #canvas3d ~ a,
        canvas + a,
        canvas ~ a,
        a[aria-label*="Spline" i],
        a[title*="Spline" i],
        div[class*="watermark" i],
        div[class*="spline" i] {
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
            width: 0 !important;
            height: 0 !important;
            position: absolute !important;
            left: -99999px !important;
            top: -99999px !important;
            z-index: -99999 !important;
        }

        .bg-fallback {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            background-image: url('https://cdn.21st.dev/assets/mirror/c3/c333918af688a4a8a3d004652e6c0ee219457a9d84d380eeb31f513d4b59a09f.png');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        .bg-vignette {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 1;
            pointer-events: none;
            background: radial-gradient(circle at 50% 45%, rgba(6, 7, 9, 0.15) 0%, rgba(6, 7, 9, 0.85) 100%);
        }

        /* App Layout Shell */
        .app-shell {
            position: relative;
            z-index: 2;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Top Navigation Bar */
        .ruixen-navbar {
            height: 64px;
            padding: 0 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(8, 9, 12, 0.45);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-glass);
            flex-shrink: 0;
        }

        .nav-brand-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: #fff;
            cursor: pointer;
        }

        .brand-logo-wrap {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            filter: drop-shadow(0 0 10px rgba(129, 140, 248, 0.6));
        }

        .logo-ring-outer {
            transform-origin: 16px 16px;
            animation: spinRing 24s linear infinite;
        }

        .logo-ring-inner {
            transform-origin: 16px 16px;
            animation: spinRingRev 14s linear infinite;
        }

        @keyframes spinRing {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes spinRingRev {
            from { transform: rotate(360deg); }
            to { transform: rotate(0deg); }
        }

        .brand-name {
            font-size: 1.12rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: linear-gradient(135deg, #ffffff 40%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-badge {
            font-size: 0.72rem;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 9999px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.16);
            color: var(--text-sub);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.2s ease;
        }

        .brand-badge:hover {
            background: rgba(255, 255, 255, 0.16);
            border-color: rgba(255, 255, 255, 0.35);
            color: #ffffff;
            transform: translateY(-1px);
            box-shadow: 0 2px 12px rgba(255, 255, 255, 0.15);
        }

        /* Floating Creator GitHub Badge in bottom-right corner */
        .creator-badge {
            position: fixed;
            bottom: 16px;
            right: 20px;
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 7px;
            padding: 6px 14px;
            border-radius: 9999px;
            background: rgba(10, 11, 15, 0.78);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: var(--text-sub);
            font-size: 0.75rem;
            font-weight: 500;
            text-decoration: none;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            transition: all 0.25s ease;
        }

        .creator-badge:hover {
            background: rgba(255, 255, 255, 0.14);
            border-color: rgba(255, 255, 255, 0.35);
            color: #ffffff;
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(129, 140, 248, 0.3);
        }

        .nav-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.82rem;
            color: var(--text-muted);
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 10px var(--green);
        }

        .nav-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .nav-btn {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-glass);
            color: #e5e7eb;
            padding: 8px 15px;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 7px;
            text-decoration: none;
            transition: all 0.2s ease;
        }

        .nav-btn:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: var(--border-hover);
            color: #fff;
            transform: translateY(-1px);
        }

        /* Hero Centered Section (Empty State) */
        .hero-section {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .hero-title {
            font-size: 3rem;
            font-weight: 600;
            letter-spacing: -0.03em;
            color: #ffffff;
            margin-bottom: 12px;
            text-shadow: 0 2px 14px rgba(0, 0, 0, 0.7);
        }

        .hero-subtitle {
            font-size: 1.1rem;
            color: #d1d5db;
            max-width: 600px;
            line-height: 1.5;
            margin-bottom: 36px;
            text-shadow: 0 1px 8px rgba(0, 0, 0, 0.6);
        }

        /* 21st.dev Quorum Chat Input Container */
        .ruixen-input-wrap {
            width: 100%;
            max-width: 780px;
        }

        .ruixen-card {
            background: var(--card-glass);
            backdrop-filter: blur(28px);
            -webkit-backdrop-filter: blur(28px);
            border: 1px solid var(--border-glass);
            border-radius: 18px;
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.12);
            transition: border-color 0.2s, box-shadow 0.2s;
            overflow: hidden;
        }

        .ruixen-card:focus-within {
            border-color: rgba(255, 255, 255, 0.35);
            box-shadow: 0 28px 70px rgba(0, 0, 0, 0.8), 0 0 35px rgba(255, 255, 255, 0.1);
        }

        .ruixen-textarea {
            width: 100%;
            min-height: 52px;
            max-height: 160px;
            padding: 16px 20px 8px 20px;
            background: transparent;
            border: none;
            outline: none;
            resize: none;
            color: #ffffff;
            font-size: 0.96rem;
            line-height: 1.5;
            font-family: inherit;
        }

        .ruixen-textarea::placeholder {
            color: #9ca3af;
        }

        .ruixen-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 18px 14px 18px;
        }

        .footer-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .model-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.78rem;
            font-weight: 500;
            color: #9ca3af;
        }

        .footer-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .send-btn {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: #ffffff;
            border: none;
            color: #000000;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .send-btn:disabled {
            background: #27272a;
            color: #71717a;
            cursor: not-allowed;
        }

        .send-btn:not(:disabled):hover {
            background: #f3f4f6;
            transform: scale(1.05);
            box-shadow: 0 0 18px rgba(255, 255, 255, 0.45);
        }

        /* 21st.dev Quick Action Buttons */
        .quick-actions-row {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 24px;
        }

        .quick-pill {
            background: rgba(14, 15, 20, 0.65);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #d1d5db;
            padding: 8px 16px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }

        .quick-pill:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.32);
            color: #ffffff;
            transform: translateY(-1px);
        }

        /* Active Chat Section */
        .chat-section {
            flex: 1;
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
            height: calc(100vh - 64px);
            overflow: hidden;
            position: relative;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px 20px 140px 20px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            scrollbar-width: thin;
            scrollbar-color: rgba(255,255,255,0.2) transparent;
        }

        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        .chat-messages::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.2);
            border-radius: 9999px;
        }

        /* Message Bubbles */
        .msg-row {
            display: flex;
            width: 100%;
            animation: fadeIn 0.25s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .msg-row.user {
            justify-content: flex-end;
        }

        .user-bubble {
            max-width: 78%;
            background: rgba(255, 255, 255, 0.14);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid rgba(255, 255, 255, 0.24);
            color: #ffffff;
            padding: 12px 18px;
            border-radius: 20px 20px 4px 20px;
            font-size: 0.96rem;
            line-height: 1.5;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }

        .msg-row.ai {
            justify-content: flex-start;
        }

        .ai-bubble {
            max-width: 94%;
            width: 94%;
            background: rgba(12, 13, 18, 0.78);
            backdrop-filter: blur(28px);
            -webkit-backdrop-filter: blur(28px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 20px 20px 20px 4px;
            padding: 20px 24px;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.5);
        }

        /* Live Status Bar */
        .status-badge-live {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.82rem;
            color: #a1a1aa;
            margin-bottom: 12px;
            padding: 4px 12px;
            border-radius: 9999px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .typing-dots {
            display: inline-flex;
            gap: 4px;
        }

        .typing-dots span {
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: #ffffff;
            animation: bounce 1.2s infinite ease-in-out;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1.2); opacity: 1; }
        }

        /* Rich Markdown Typography */
        .content-body h1, .content-body h2, .content-body h3, .content-body h4 {
            margin-top: 16px;
            margin-bottom: 8px;
            color: #ffffff;
            font-weight: 600;
        }
        .content-body h3 { font-size: 1.15rem; }
        .content-body h4 { font-size: 1.05rem; }
        .content-body p { margin-bottom: 12px; line-height: 1.65; color: #e4e4e7; }
        .content-body ul, .content-body ol {
            margin-left: 22px;
            margin-bottom: 14px;
            color: #e4e4e7;
        }
        .content-body li { margin-bottom: 6px; }
        .content-body blockquote {
            border-left: 3px solid #ffffff;
            padding-left: 14px;
            color: #a1a1aa;
            margin: 12px 0;
        }

        /* Beautiful Dark Glass Tables */
        .content-body table {
            width: 100%;
            border-collapse: collapse;
            margin: 18px 0;
            font-size: 0.88rem;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.14);
        }
        .content-body th {
            background: rgba(255, 255, 255, 0.09);
            color: #ffffff;
            font-weight: 600;
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.14);
            text-align: left;
        }
        .content-body td {
            padding: 11px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            color: #d4d4d8;
        }
        .content-body tr:last-child td { border-bottom: none; }
        .content-body tr:hover td { background: rgba(255, 255, 255, 0.04); }
        .content-body code {
            background: rgba(255, 255, 255, 0.08);
            padding: 2px 6px;
            border-radius: 5px;
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            color: #f43f5e;
        }

        /* Verification & Citations Footer */
        .verification-bar {
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            font-size: 0.82rem;
        }

        .badge-conf {
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.78rem;
        }
        .badge-green { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
        .badge-yellow { background: rgba(234, 179, 8, 0.15); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); }
        .badge-red { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }

        .sources-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }

        .source-chip {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 5px 10px;
            border-radius: 8px;
            font-size: 0.75rem;
            color: #d4d4d8;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        /* Docked Bottom Input Capsule */
        .docked-input-wrap {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 820px;
            padding: 0 20px;
            z-index: 10;
        }

        /* ========================================================
           Mobile Responsiveness & Adaptive Viewport Media Queries
           ======================================================== */
        
        /* MathJax and Table Mobile Scroll Wrappers */
        .content-body table {
            display: block;
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }

        mjx-container, .MathJax {
            overflow-x: auto !important;
            overflow-y: hidden !important;
            max-width: 100% !important;
            padding: 2px 0;
        }

        /* Tablets & Medium Screens (< 860px) */
        @media (max-width: 860px) {
            .ruixen-navbar {
                padding: 0 18px;
            }

            .nav-status {
                display: none; /* Hide long engine string on medium displays */
            }

            .hero-title {
                font-size: 2.3rem;
            }

            .ruixen-input-wrap {
                max-width: 92%;
            }
        }

        /* Mobile Phones (< 640px) */
        @media (max-width: 640px) {
            .app-shell {
                height: 100dvh; /* Adaptive dynamic viewport height for mobile browsers */
            }

            .ruixen-navbar {
                height: 56px;
                padding: 0 12px;
            }

            .nav-brand-group {
                gap: 8px;
            }

            .brand-name {
                font-size: 1rem;
            }

            .brand-badge {
                font-size: 0.65rem;
                padding: 3px 7px;
            }

            .nav-actions {
                gap: 6px;
            }

            .nav-btn {
                padding: 6px 10px;
                font-size: 0.75rem;
            }

            /* Hide button text labels on mobile to keep icons clean and compact */
            .nav-btn span {
                display: none;
            }

            /* Hero adjustments */
            .hero-section {
                padding: 16px 12px;
                justify-content: center;
            }

            .hero-title {
                font-size: 1.85rem;
                letter-spacing: -0.02em;
                margin-bottom: 6px;
            }

            .hero-subtitle {
                font-size: 0.92rem;
                margin-bottom: 22px;
                padding: 0 8px;
            }

            .ruixen-input-wrap {
                max-width: 100%;
                padding: 0 4px;
            }

            .ruixen-card {
                border-radius: 16px;
            }

            .ruixen-textarea {
                font-size: 0.9rem;
                padding: 12px 14px 6px 14px;
                min-height: 48px;
            }

            .ruixen-footer {
                padding: 8px 12px 10px 12px;
            }

            .model-chip {
                font-size: 0.72rem;
            }

            .send-btn {
                width: 32px;
                height: 32px;
            }

            /* Horizontal touch-scrollable quick action pills */
            .quick-actions-row {
                justify-content: flex-start;
                flex-wrap: nowrap;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                padding: 4px 6px 12px 6px;
                width: 100%;
                margin-top: 16px;
                scrollbar-width: none;
            }

            .quick-actions-row::-webkit-scrollbar {
                display: none;
            }

            .quick-pill {
                flex-shrink: 0;
                padding: 7px 13px;
                font-size: 0.75rem;
            }

            /* Active Chat View */
            .chat-section {
                height: calc(100dvh - 56px);
            }

            .chat-messages {
                padding: 14px 10px 115px 10px;
                gap: 16px;
            }

            .user-bubble {
                max-width: 88%;
                font-size: 0.9rem;
                padding: 10px 14px;
                border-radius: 16px 16px 4px 16px;
            }

            .ai-bubble {
                max-width: 100%;
                width: 100%;
                padding: 14px 14px;
                border-radius: 16px 16px 16px 4px;
            }

            .content-body p, .content-body li {
                font-size: 0.9rem;
                line-height: 1.55;
            }

            .docked-input-wrap {
                bottom: 10px;
                padding: 0 10px;
                padding-bottom: env(safe-area-inset-bottom, 0px);
            }

            /* Hide creator badge during active chat to prevent blocking docked input on small screens */
            body.chat-active .creator-badge {
                display: none !important;
            }

            .creator-badge {
                bottom: 8px;
                right: 12px;
                padding: 4px 10px;
                font-size: 0.68rem;
            }
        }
    </style>
</head>
<body>
    <!-- Fallback Background Image from 21st.dev -->
    <div class="bg-fallback"></div>

    <!-- 3D Spline Interactive Canvas -->
    <canvas id="canvas3d"></canvas>

    <!-- Dark Vignette Overlay for Readability -->
    <div class="bg-vignette"></div>

    <div class="app-shell">
        <!-- Ruixen Navbar -->
        <nav class="ruixen-navbar">
            <div class="nav-brand-group">
                <a href="#" class="nav-brand" onclick="location.reload()" title="Refresh Application">
                    <span class="brand-logo-wrap">
                        <svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <defs>
                                <linearGradient id="qGrad1" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                                    <stop offset="0%" stop-color="#38bdf8" />
                                    <stop offset="50%" stop-color="#818cf8" />
                                    <stop offset="100%" stop-color="#c084fc" />
                                </linearGradient>
                                <linearGradient id="qGrad2" x1="28" y1="4" x2="4" y2="28" gradientUnits="userSpaceOnUse">
                                    <stop offset="0%" stop-color="#c084fc" />
                                    <stop offset="100%" stop-color="#38bdf8" />
                                </linearGradient>
                            </defs>
                            <circle class="logo-ring-outer" cx="16" cy="16" r="13" stroke="url(#qGrad1)" stroke-width="1.8" stroke-dasharray="26 8 10 8" />
                            <circle class="logo-ring-inner" cx="16" cy="16" r="8.5" stroke="url(#qGrad2)" stroke-width="1.5" stroke-dasharray="14 8" />
                            <circle cx="16" cy="16" r="3.2" fill="#ffffff" />
                            <circle cx="16" cy="16" r="1.5" fill="#38bdf8" />
                        </svg>
                    </span>
                    <span class="brand-name">Quorum AI</span>
                </a>
                <a href="https://github.com/athrvmrjkr" target="_blank" rel="noopener noreferrer" class="brand-badge" title="Open @athrvmrjkr on GitHub">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                    <span>@athrvmrjkr</span>
                </a>
            </div>

            <div class="nav-status">
                <span class="status-dot"></span>
                <span>Groq 70B • Qdrant Cloud • Anti-Hallucination Critic</span>
            </div>

            <div class="nav-actions">
                <button type="button" class="nav-btn" onclick="startNewChat()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    <span>New Chat</span>
                </button>
                <button type="button" class="nav-btn" onclick="downloadChatTranscript()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    <span>Export (.md)</span>
                </button>
                <a class="nav-btn" href="https://logfire-us.pydantic.dev/atharvamirajkar-mscds/pdfrag" target="_blank" rel="noopener">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2c1.1 0 2 .9 2 2 0 .5-.2 1-.5 1.4L10 10l5 2 4.5-4.5c.4-.4.9-.5 1.5-.5 1.1 0 2 .9 2 2 0 2-4 9-11 9S2 13 2 10c0-1.1.9-2 2-2 .6 0 1.1.2 1.5.6L10 13l-2-5-3.5-4.6C4.2 3 4 2.5 4 2c0-1.1.9-2 2-2h6z"/></svg>
                    <span>Logfire</span>
                </a>
            </div>
        </nav>

        <!-- Centered Empty Hero State (Signature 21st.dev Ruixen Moon Chat) -->
        <main id="heroSection" class="hero-section">
            <h1 class="hero-title">Quorum AI</h1>
            <p class="hero-subtitle">Every answer, checked against your sources.</p>

            <div class="ruixen-input-wrap">
                <div class="ruixen-card">
                    <textarea id="heroInput" class="ruixen-textarea" placeholder="Ask about Deep Learning, Transformers, Statistics, or System Design..." rows="1"></textarea>
                    <div class="ruixen-footer">
                        <div class="footer-left">
                            <span class="model-chip">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                                Anti-Hallucination Critic Active
                            </span>
                        </div>
                        <div class="footer-right">
                            <button type="button" id="heroSendBtn" class="send-btn" onclick="submitHeroQuery()" disabled>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Quick Action Buttons from 21st.dev -->
                <div class="quick-actions-row">
                    <button type="button" class="quick-pill" onclick="sendQuickPrompt('Explain the difference between self-attention and multi-head attention. Include mathematical formulas and compare them in a markdown table.')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                        <span>Self-Attention vs Multi-Head</span>
                    </button>
                    <button type="button" class="quick-pill" onclick="sendQuickPrompt('What is the definition and mathematical formula of variance and standard deviation of a random variable X?')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/></svg>
                        <span>Variance & Std Deviation Math</span>
                    </button>
                    <button type="button" class="quick-pill" onclick="sendQuickPrompt('Explain replication vs partitioning in distributed data stores. Compare them in a markdown table.')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
                        <span>Replication vs Partitioning</span>
                    </button>
                    <button type="button" class="quick-pill" onclick="sendQuickPrompt('Explain the scaled dot-product attention formula in transformers.')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                        <span>Scaled Dot-Product Math</span>
                    </button>
                </div>
            </div>
        </main>

        <!-- Active Chat Section (Revealed when messages exist) -->
        <section id="chatSection" class="chat-section" style="display: none;">
            <div id="messagesContainer" class="chat-messages"></div>

            <!-- Docked Floating Input Capsule -->
            <div class="docked-input-wrap">
                <div class="ruixen-card">
                    <textarea id="dockedInput" class="ruixen-textarea" placeholder="Ask a follow-up question..." rows="1"></textarea>
                    <div class="ruixen-footer">
                        <div class="footer-left">
                            <span class="model-chip">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                                Anti-Hallucination Critic Active
                            </span>
                        </div>
                        <div class="footer-right">
                            <button type="button" id="dockedSendBtn" class="send-btn" onclick="submitDockedQuery()" disabled>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>

    <!-- Floating Creator Badge in bottom-right corner -->
    <a href="https://github.com/athrvmrjkr" target="_blank" rel="noopener noreferrer" class="creator-badge" id="creatorBadge" title="Open @athrvmrjkr on GitHub">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        <span>Built by @athrvmrjkr</span>
    </a>

    <!-- Spline 3D Scene Runtime Initialization & Watermark Purge -->
    <script type="module">
        import { Application } from 'https://unpkg.com/@splinetool/runtime@1.9.72/build/runtime.js';
        const canvas = document.getElementById('canvas3d');
        try {
            const app = new Application(canvas, { htmlContentMode: 'inline' });
            app.load('https://prod.spline.design/b0kwxkzX1UnCevUN/scene.splinecode');
        } catch (err) {
            console.warn('Spline 3D load fallback:', err);
        }

        // Active purge of any injected "Built with Spline" watermark badge or links
        function purgeSplineLogo() {
            try {
                const candidates = document.querySelectorAll('a[href*="spline"], #spline-logo, .spline-watermark, #canvas3d + a, #canvas3d ~ a, canvas + a');
                candidates.forEach(el => {
                    if (el.id !== 'creatorBadge') el.remove();
                });
                document.querySelectorAll('a').forEach(a => {
                    if (a.id === 'creatorBadge') return;
                    const txt = (a.innerText || a.textContent || '').toLowerCase();
                    const href = (a.href || '').toLowerCase();
                    if (txt.includes('spline') || href.includes('spline')) {
                        a.remove();
                    }
                });
                // Check shadow roots if custom element or shadow DOM is used
                document.querySelectorAll('*').forEach(node => {
                    if (node.shadowRoot) {
                        const shadowLogo = node.shadowRoot.querySelector('#logo, #spline-logo, a[href*="spline"], a');
                        if (shadowLogo) shadowLogo.remove();
                    }
                });
            } catch (e) {}
        }
        setInterval(purgeSplineLogo, 50);
        window.addEventListener('DOMContentLoaded', purgeSplineLogo);
        window.addEventListener('load', purgeSplineLogo);
        const splineObserver = new MutationObserver(purgeSplineLogo);
        splineObserver.observe(document.documentElement, { childList: true, subtree: true });
    </script>

    <script>
        const heroSection = document.getElementById("heroSection");
        const chatSection = document.getElementById("chatSection");
        const messagesContainer = document.getElementById("messagesContainer");
        const heroInput = document.getElementById("heroInput");
        const heroSendBtn = document.getElementById("heroSendBtn");
        const dockedInput = document.getElementById("dockedInput");
        const dockedSendBtn = document.getElementById("dockedSendBtn");

        let chatHistory = [];

        // Auto-Resize Textarea
        function autoResize(el, minH = 52, maxH = 160) {
            el.style.height = minH + 'px';
            const newH = Math.max(minH, Math.min(el.scrollHeight, maxH));
            el.style.height = newH + 'px';
        }

        [heroInput, dockedInput].forEach(inp => {
            inp.addEventListener("input", function() {
                autoResize(this);
                const hasText = this.value.trim().length > 0;
                if (this === heroInput) heroSendBtn.disabled = !hasText;
                if (this === dockedInput) dockedSendBtn.disabled = !hasText;
            });
            inp.addEventListener("keydown", function(e) {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (this.value.trim().length > 0) {
                        if (this === heroInput) submitHeroQuery();
                        if (this === dockedInput) submitDockedQuery();
                    }
                }
            });
        });

        let mathJaxQueue = Promise.resolve();
        function renderMath(targetElement) {
            const el = targetElement || document.body;
            if (window.MathJax && window.MathJax.typesetPromise) {
                mathJaxQueue = mathJaxQueue.then(() => {
                    return window.MathJax.typesetPromise([el]);
                }).catch(function (err) {
                    console.warn('MathJax error:', err);
                });
            }
        }

        function scrollToBottom() {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function startNewChat() {
            chatHistory = [];
            messagesContainer.innerHTML = "";
            chatSection.style.display = "none";
            heroSection.style.display = "flex";
            document.body.classList.remove("chat-active");
            heroInput.value = "";
            heroInput.style.height = "52px";
            heroSendBtn.disabled = true;
            heroInput.focus();
        }

        function downloadChatTranscript() {
            if (chatHistory.length === 0) {
                alert("No messages to download yet!");
                return;
            }

            let mdContent = "# Quorum AI - Multi-Agent Research Transcript\n";
            mdContent += "Generated on: " + new Date().toLocaleString() + "\n\n---\n\n";

            chatHistory.forEach(item => {
                const role = item.role === "user" ? "### 👤 User" : "### 🤖 Quorum AI";
                mdContent += role + "\n\n" + item.content + "\n\n---\n\n";
            });

            const blob = new Blob([mdContent], { type: "text/markdown;charset=utf-8;" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = `ruixen_transcript_${Date.now()}.md`;
            link.click();
        }

        function sendQuickPrompt(promptText) {
            heroInput.value = promptText;
            submitHeroQuery();
        }

        function submitHeroQuery() {
            const text = heroInput.value.trim();
            if (!text) return;
            document.body.classList.add("chat-active");
            heroSection.style.display = "none";
            chatSection.style.display = "flex";
            handleSend(text);
            heroInput.value = "";
            heroSendBtn.disabled = true;
        }

        function submitDockedQuery() {
            const text = dockedInput.value.trim();
            if (!text) return;
            document.body.classList.add("chat-active");
            dockedInput.value = "";
            dockedInput.style.height = "52px";
            dockedSendBtn.disabled = true;
            handleSend(text);
        }

        function sanitizeMathAndLatex(rawText) {
            if (!rawText) return "";
            let text = rawText.replace(/\x0c/g, '\\f').replace(/\x08/g, '\\b');

            // 1. Fix Greek letters erroneously prefixed with dollar sign instead of backslash ($alpha -> \alpha)
            const greekLetters = [
                'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta',
                'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'pi', 'rho', 'sigma',
                'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega'
            ];
            greekLetters.forEach(g => {
                text = text.replace(new RegExp('\\$' + g + '(?=[^a-zA-Z]|$)', 'g'), '\\' + g);
            });

            // 2. Fix nested dollar sign anomalies: $$ $...$ $$ or $$ $...$$ or $$...$ $$
            text = text.replace(/\$\$\s*\$([\s\S]*?)\$\s*\$\$/g, '$$$$ $1 $$$$');
            text = text.replace(/\$\$\s*\$([\s\S]*?)\$\$/g, '$$$$ $1 $$$$');
            text = text.replace(/\$\$\s*([\s\S]*?)\$\s*\$\$/g, '$$$$ $1 $$$$');

            // 3. Fix \operatorname{softmax}! or \operatorname{softmax}!\(
            text = text.replace(/\\operatorname\{softmax\}!\s*\\left\(/g, '\\operatorname{softmax}\\left(');
            text = text.replace(/\\operatorname\{softmax\}!\s*\(/g, '\\operatorname{softmax}(');
            text = text.replace(/\\operatorname\{softmax\}!/g, '\\operatorname{softmax}');

            // 4. Fix missing subscripts on common Transformer symbols
            // e.g. \text{head}i -> \text{head}_i, \text{head}1 -> \text{head}_1, \text{head}h -> \text{head}_h
            text = text.replace(/\\text\{head\}([0-9a-zA-Z])(?![a-zA-Z])/g, '\\text{head}_$1');
            // e.g. \text{scores}i -> \text{scores}_i
            text = text.replace(/\\text\{scores\}([0-9a-zA-Z])(?![a-zA-Z])/g, '\\text{scores}_$1');
            // e.g. d{\text{head}} or d\text{head} -> d_{\text{head}}
            text = text.replace(/d\{\\text\{([a-zA-Z0-9_]+)\}\}/g, 'd_{\\text{$1}}');
            text = text.replace(/d\\text\{([a-zA-Z0-9_]+)\}/g, 'd_{\\text{$1}}');
            // e.g. K''i{}^\top -> K''_{i}^{\top}, V''i -> V''_i, Q''i -> Q''_i
            text = text.replace(/([QKV]''?)\s*([0-9a-zA-Z])(?=[{^\s,\.]|$)/g, '$1_$2');
            // e.g. stray semicolons around arrows like ;\xrightarrow{view};
            text = text.replace(/;\s*\\xrightarrow\{([^}]+)\}\s*;/g, '\\xrightarrow{$1}');

            // 5. Convert LaTeX bracket delimiters: \[ ... \] to $$ ... $$ and \( ... \) to $ ... $
            text = text.replace(/\\\[([\s\S]*?)\\\]/g, '$$$$$1$$$$');
            text = text.replace(/\\\(([\s\S]*?)\\\)/g, '$$$1$$');

            // 6. Fix unclosed bracket cutoffs at the end of the response: e.g. [ \text{context} or \[ \text{context}
            text = text.replace(/(\[|\\\[)\s*(\\text\{[^\n\]]+\})\s*$/g, '$$$$ $2 $$$$');

            // 7. Auto-close dangling open math tags if generation cuts off
            const blockMatches = text.match(/\$\$/g);
            if (blockMatches && blockMatches.length % 2 !== 0) {
                text += '\n$$';
            }
            const strippedForSingle = text.replace(/\$\$[\s\S]*?\$\$/g, '');
            const singleMatches = strippedForSingle.match(/\$/g);
            if (singleMatches && singleMatches.length % 2 !== 0) {
                text += '$';
            }

            return text;
        }

        function formatMarkdown(rawText) {
            if (!rawText) return "";
            let text = sanitizeMathAndLatex(rawText);

            // Inside table rows, ensure block math $$...$$ is converted to inline $...$
            const lines = text.split('\n');
            const fixedLines = lines.map(line => {
                if (line.trim().startsWith('|')) {
                    return line.replace(/\$\$(.*?)\$\$/g, '$$$1$$');
                }
                return line;
            });
            text = fixedLines.join('\n');

            // PROTECT MATH FROM MARKED.JS:
            // Extract $$...$$ and $...$ before marked parses, so marked does NOT turn _i into <em>i</em>
            const mathPlaceholders = [];
            
            // Extract block math $$ ... $$
            text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, eq) => {
                const placeholder = `%%%MATH_BLOCK_${mathPlaceholders.length}%%%`;
                mathPlaceholders.push({ placeholder, formula: `$$${eq}$$` });
                return placeholder;
            });

            // Extract inline math $ ... $
            text = text.replace(/\$([^\$\n]+?)\$/g, (match, eq) => {
                const placeholder = `%%%MATH_INLINE_${mathPlaceholders.length}%%%`;
                mathPlaceholders.push({ placeholder, formula: `$${eq}$` });
                return placeholder;
            });

            // Parse Markdown safely
            let html = (typeof marked !== 'undefined') ? marked.parse(text) : escapeHtml(text).replace(/\n/g, '<br>');

            // Restore all mathematical equations intact
            mathPlaceholders.forEach(item => {
                html = html.replace(item.placeholder, item.formula);
            });

            return html;
        }

        async function handleSend(text) {
            dockedInput.disabled = true;
            dockedSendBtn.disabled = true;

            // Render User Bubble
            const userRow = document.createElement("div");
            userRow.className = "msg-row user";
            userRow.innerHTML = `<div class="user-bubble">${escapeHtml(text)}</div>`;
            messagesContainer.appendChild(userRow);
            scrollToBottom();

            // Render AI Bubble with Live Streaming Container
            const aiRow = document.createElement("div");
            aiRow.className = "msg-row ai";
            aiRow.innerHTML = `
                <div class="ai-bubble">
                    <div class="status-badge-live">
                        <div class="typing-dots"><span></span><span></span><span></span></div>
                        <span class="status-msg">Checking domain relevance...</span>
                    </div>
                    <div class="content-body"></div>
                    <div class="footer-meta"></div>
                </div>
            `;
            messagesContainer.appendChild(aiRow);
            scrollToBottom();

            const bubble = aiRow.querySelector(".ai-bubble");
            const statusBadge = bubble.querySelector(".status-badge-live");
            const statusMsg = bubble.querySelector(".status-msg");
            const contentBody = bubble.querySelector(".content-body");
            const footerMeta = bubble.querySelector(".footer-meta");

            let accumulatedText = "";
            let streamSuccess = false;

            try {
                const response = await fetch("/api/chat/stream", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: text, history: chatHistory })
                });

                if (!response.ok) {
                    throw new Error("Server error status: " + response.status);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split("\n");
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (!line.trim()) continue;
                        try {
                            const event = JSON.parse(line);
                            if (event.type === "status") {
                                if (statusMsg) statusMsg.innerText = event.message;
                            } else if (event.type === "token") {
                                if (statusBadge && statusBadge.style.display !== "none") {
                                    statusBadge.style.display = "none";
                                }
                                accumulatedText += event.token;
                                contentBody.innerHTML = formatMarkdown(accumulatedText);
                                scrollToBottom();
                            } else if (event.type === "refusal" || event.type === "empty") {
                                if (statusBadge) statusBadge.style.display = "none";
                                accumulatedText = event.message;
                                contentBody.innerHTML = formatMarkdown(accumulatedText);
                                scrollToBottom();
                            } else if (event.type === "replace_answer") {
                                accumulatedText = event.answer;
                                contentBody.innerHTML = formatMarkdown(accumulatedText);
                                scrollToBottom();
                            } else if (event.type === "verification") {
                                streamSuccess = true;
                                if (statusBadge) statusBadge.style.display = "none";

                                let badgeClass = "badge-red";
                                if (event.confidence >= 80) badgeClass = "badge-green";
                                else if (event.confidence >= 60) badgeClass = "badge-yellow";

                                let sourcesHtml = "";
                                if (event.sources && event.sources.length > 0) {
                                    sourcesHtml = '<div class="sources-grid">';
                                    event.sources.forEach(s => {
                                        const srcName = s.filename || s.source || "Document";
                                        sourcesHtml += `
                                            <div class="source-chip">
                                                <span>📄 ${escapeHtml(srcName)}</span>
                                                <span style="opacity:0.6;">(p. ${s.page})</span>
                                            </div>
                                        `;
                                    });
                                    sourcesHtml += '</div>';
                                }

                                footerMeta.innerHTML = `
                                    <div class="verification-bar">
                                        <span class="badge-conf ${badgeClass}">Confidence: ${event.confidence}%</span>
                                        <span style="color:#a1a1aa;">${escapeHtml(event.reasoning || '')}</span>
                                    </div>
                                    ${sourcesHtml}
                                `;

                                chatHistory.push({ role: "user", content: text });
                                chatHistory.push({ role: "assistant", content: accumulatedText });

                                renderMath(bubble);
                                scrollToBottom();
                            }
                        } catch (parseErr) {
                            console.warn("Stream line parse error:", parseErr, line);
                        }
                    }
                }

                if (!streamSuccess) {
                    if (statusBadge) statusBadge.style.display = "none";
                    renderMath(bubble);
                    if (accumulatedText) {
                        chatHistory.push({ role: "user", content: text });
                        chatHistory.push({ role: "assistant", content: accumulatedText });
                    }
                }

            } catch (err) {
                bubble.innerHTML = `
                    <div style="color: var(--red); padding: 12px;">Error retrieving response: ${escapeHtml(err.message)}</div>
                `;
            } finally {
                dockedInput.disabled = false;
                dockedInput.focus();
                scrollToBottom();
            }
        }

        function escapeHtml(str) {
            if (!str) return '';
            return str
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
"""
