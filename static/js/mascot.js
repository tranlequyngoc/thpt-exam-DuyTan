
    // ═══ ON THI CHAN - Mascot ═══
    (function(){
    const MASCOT_HTML = `
    <div id="mascot" style="position:fixed;bottom:20px;right:20px;z-index:9999;cursor:pointer;transition:.3s" onclick="mascotClick()">
      <div id="mascotBubble" style="display:none;position:absolute;bottom:75px;right:0;background:#fff;border-radius:16px 16px 4px 16px;padding:12px 16px;box-shadow:0 4px 20px rgba(0,0,0,0.15);max-width:250px;font-size:13px;line-height:1.5;color:#333;animation:bubbleIn .3s ease">
        <div style="font-weight:700;color:#764ba2;margin-bottom:4px;font-size:11px">On Thi Chan:</div>
        <div id="mascotText">Loading...</div>
      </div>
      <div id="mascotBody" style="width:65px;height:65px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:32px;box-shadow:0 4px 20px rgba(102,126,234,0.4);transition:.3s;animation:mascotFloat 3s ease-in-out infinite">
        🤖
      </div>
    </div>
    <style>
    @keyframes mascotFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
    @keyframes bubbleIn{from{opacity:0;transform:scale(0.8) translateY(10px)}to{opacity:1;transform:scale(1) translateY(0)}}
    @keyframes celebrate{0%{transform:scale(1)}25%{transform:scale(1.2) rotate(-5deg)}50%{transform:scale(1.3) rotate(5deg)}75%{transform:scale(1.2) rotate(-3deg)}100%{transform:scale(1)}}
    #mascot:hover #mascotBody{transform:scale(1.1);box-shadow:0 6px 30px rgba(102,126,234,0.6)}
    </style>`;
    
    document.body.insertAdjacentHTML('beforeend', MASCOT_HTML);
    
    let bubbleTimer = null;
    let autoTimer = null;
    
    window.mascotClick = function() {
        fetch('/api/mascot?action=idle')
            .then(r => r.json())
            .then(d => showBubble(d.message))
            .catch(() => showBubble('Hoc di ban oi!'));
    };
    
    window.mascotSay = function(text, duration) {
        showBubble(text, duration || 5000);
    };
    
    window.mascotCelebrate = function() {
        const body = document.getElementById('mascotBody');
        body.style.animation = 'celebrate .5s ease';
        setTimeout(() => body.style.animation = 'mascotFloat 3s ease-in-out infinite', 600);
    };
    
    window.mascotCorrect = function() {
        fetch('/api/mascot?action=correct')
            .then(r => r.json())
            .then(d => { showBubble(d.message, 3000); mascotCelebrate(); })
            .catch(() => {});
    };
    
    window.mascotWrong = function() {
        fetch('/api/mascot?action=wrong')
            .then(r => r.json())
            .then(d => showBubble(d.message, 3000))
            .catch(() => {});
    };
    
    function showBubble(text, duration) {
        const bubble = document.getElementById('mascotBubble');
        const textEl = document.getElementById('mascotText');
        textEl.textContent = text;
        bubble.style.display = 'block';
        if (bubbleTimer) clearTimeout(bubbleTimer);
        bubbleTimer = setTimeout(() => { bubble.style.display = 'none'; }, duration || 6000);
    }
    
    // Auto show message every 60s
    function autoMessage() {
        fetch('/api/mascot?action=idle')
            .then(r => r.json())
            .then(d => showBubble(d.message, 8000))
            .catch(() => {});
    }
    
    // First message after 5s
    setTimeout(autoMessage, 5000);
    // Then every 90s
    autoTimer = setInterval(autoMessage, 90000);
    
    })();
    