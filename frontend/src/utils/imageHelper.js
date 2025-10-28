// frontend/src/utils/imageHelper.js

export const getImageUrl = (imagePath) => {
  if (!imagePath) return '/static/img/product/placeholder.jpg';

  // If it's already a full URL, return as is
  if (imagePath.startsWith('http')) return imagePath;

  // Convert backend upload paths to frontend static paths
  if (imagePath.startsWith('/uploads/product/')) {
    const filename = imagePath.split('/').pop();
    return `/static/img/products/${filename}`;
  }

  if (imagePath.startsWith('/uploads/categories/')) {
    const filename = imagePath.split('/').pop();
    return `/static/img/categories/${filename}`;
  }

  // If it's already a frontend static path, use as is
  if (imagePath.startsWith('/static/')) {
    return imagePath;
  }

  // Default fallback
  return '/static/img/product/placeholder.jpg';
};

export const getCategoryImageUrl = (imagePath) => {
  if (!imagePath) return '/static/img/categories/placeholder.jpg';

  if (imagePath.startsWith('http')) return imagePath;

  if (imagePath.startsWith('/uploads/categories/')) {
    const filename = imagePath.split('/').pop();
    return `/static/img/categories/${filename}`;
  }

  if (imagePath.startsWith('/static/')) {
    return imagePath;
  }

  return '/static/img/categories/placeholder.jpg';
};