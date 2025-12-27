function changeMainImage(src, thumb) {
    document.getElementById('mainImageSrc').src = src;
    document.querySelectorAll('.hero-thumb').forEach(t => t.classList.remove('active'));
    thumb.classList.add('active');
}