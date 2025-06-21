"""
Poker game UI styles and animations
"""

POKER_STYLES = """
<style>
    .card {
        transition: all 0.3s ease;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .animate-deal {
        animation: dealCard 0.5s ease-out;
    }
    
    @keyframes dealCard {
        from {
            transform: translateY(-50px) rotate(180deg);
            opacity: 0;
        }
        to {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
        }
    }
    
    .current-player {
        border: 3px solid #3b82f6;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
    }
    
    .folded {
        opacity: 0.5;
        filter: grayscale(100%);
    }
    
    .community-card {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    }
    
    .player-card {
        background: linear-gradient(135deg, #ffffff, #f1f5f9);
    }
    
    .poker-table {
        background: linear-gradient(135deg, #059669, #047857);
        border-radius: 50%;
        padding: 2rem;
        min-height: 400px;
    }
    
    .agent-selection {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 1rem;
    }
</style>
"""
