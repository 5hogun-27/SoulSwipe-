// Swipe functionality
let currentCard = 0;
const cards = document.querySelectorAll('.card');

function showCard(index) {
    cards.forEach((card, i) => {
        card.style.display = i === index ? 'block' : 'none';
    });
}

if (cards.length > 0) {
    showCard(currentCard);
}

document.getElementById('like-btn')?.addEventListener('click', () => {
    const userId = cards[currentCard].dataset.userId;
    window.location.href = `/like/${userId}`;
});

document.getElementById('pass-btn')?.addEventListener('click', () => {
    const userId = cards[currentCard].dataset.userId;
    window.location.href = `/pass/${userId}`;
});

// Auto-scroll chat to bottom
const chatBox = document.querySelector('.chat-box');
if (chatBox) {
    chatBox.scrollTop = chatBox.scrollHeight;
}
