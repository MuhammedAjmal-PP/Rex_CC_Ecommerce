function changeMainImage(src, thumb) {
    document.getElementById('mainImageSrc').src = src;
    document.querySelectorAll('.hero-thumb').forEach(t => t.classList.remove('active'));
    thumb.classList.add('active');
}

// Zoom functionality
function zoom(event) {
    const container = document.getElementById('mainImage');
    const img = document.getElementById('mainImageSrc');
    
    if (!img) return;
    
    // Add zooming class
    container.classList.add('zooming');
    
    // Get container dimensions
    const rect = container.getBoundingClientRect();
    
    // Calculate cursor position as percentage
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    
    // Move the transform origin to cursor position
    img.style.transformOrigin = `${x}% ${y}%`;
}

function resetZoom() {
    const container = document.getElementById('mainImage');
    const img = document.getElementById('mainImageSrc');
    
    if (!container || !img) return;
    
    container.classList.remove('zooming');
    img.style.transformOrigin = 'center center';
}