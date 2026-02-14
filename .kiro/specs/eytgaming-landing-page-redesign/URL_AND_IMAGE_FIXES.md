# Landing Page URL and Image Fixes

## Issues Fixed

### 1. URL Name Errors
**Problem**: Templates were using incorrect URL names that don't exist in the URL configuration.

**Fixes Applied**:

#### Navigation Template (`templates/partials/navigation.html`)
- ❌ `{% url 'teams:team_list' %}` → ✅ `{% url 'teams:list' %}`
- ❌ `{% url 'tournaments:tournament_list' %}` → ✅ `{% url 'tournaments:list' %}`

#### Hero Section Template (`templates/partials/hero_section.html`)
- ❌ `{% url 'tournaments:tournament_list' %}` → ✅ `{% url 'tournaments:list' %}`

#### Footer Template (`templates/partials/footer.html`)
- ❌ `{% url 'privacy' %}` → ✅ `#` (placeholder)
- ❌ `{% url 'terms' %}` → ✅ `#` (placeholder)
- ❌ `{% url 'contact' %}` → ✅ `#` (placeholder)

#### News Section Template (`templates/partials/news_section.html`)
- ❌ `{% url 'news:article_list' %}` → ✅ `#news` (anchor link)

#### Merch Teaser Template (`templates/partials/merch_teaser.html`)
- ❌ `{% url 'store:product_list' %}` → ✅ `#store` (anchor link)

### 2. Missing Image File Errors
**Problem**: Templates were trying to access `.url` on image fields that have no files uploaded, causing `ValueError: The 'key_art' attribute has no file associated with it.`

**Fixes Applied**:

#### Games Section (`templates/partials/games_section.html`)
```django
{% if game.key_art %}
  <img src="{{ game.key_art.url }}" ... >
{% else %}
  <div class="w-full h-48 bg-gray-800 flex items-center justify-center">
    <span class="material-symbols-outlined text-gray-600 text-6xl">sports_esports</span>
  </div>
{% endif %}
```

#### Player Showcase (`templates/partials/player_showcase.html`)
```django
{% if player.image %}
  <img src="{{ player.image.url }}" ... >
{% else %}
  <div class="player-image bg-gray-800 flex items-center justify-center">
    <span class="material-symbols-outlined text-gray-600 text-6xl">person</span>
  </div>
{% endif %}
```

#### Media Highlights (`templates/partials/media_highlights.html`)
- Added checks for `featured_video.thumbnail`
- Added checks for `video.thumbnail`
- Shows placeholder video camera icon if missing

#### News Section (`templates/partials/news_section.html`)
```django
{% if article.image %}
  <img src="{{ article.image.url }}" ... >
{% else %}
  <div class="news-image w-full h-48 bg-gray-800 flex items-center justify-center">
    <span class="material-symbols-outlined text-gray-600 text-6xl">article</span>
  </div>
{% endif %}
```

#### Merch Teaser (`templates/partials/merch_teaser.html`)
```django
{% if product.image %}
  <img src="{{ product.image.url }}" ... >
{% else %}
  <div class="merch-image w-full h-64 flex items-center justify-center">
    <span class="material-symbols-outlined text-gray-600 text-6xl">shopping_bag</span>
  </div>
{% endif %}
```

## Result

✅ **All errors fixed!** The landing page now:
- Uses correct URL names for existing routes
- Uses placeholder anchor links for non-existent routes
- Gracefully handles missing images with Material Icons placeholders
- Will display properly even with an empty database

## Testing

The page should now load successfully at `http://127.0.0.1:8000/` without any errors, even if:
- No games, players, videos, news, or products exist in the database
- Database records exist but have no images uploaded
- Legal pages (privacy, terms, contact) don't exist yet
- Store and news apps aren't implemented yet

## Next Steps

To fully populate the landing page:
1. Add sample data via Django admin
2. Upload images for games, players, videos, news, and products
3. Implement legal pages (privacy, terms, contact) if needed
4. Implement store and news apps if needed
5. Configure social media URLs in settings.py

---

**Status**: ✅ COMPLETE  
**Date**: February 8, 2026  
**All URL and image errors resolved**
