def extract_amenities_description(listing_data):
    """
    Extract all amenity text from listing details as a simple string.
    """
    description_parts = []
    
    # Extract from details field
    if 'details' in listing_data and listing_data['details']:
        for detail_group in listing_data['details']:
            if 'text' in detail_group and isinstance(detail_group['text'], list):
                for item in detail_group['text']:
                    cleaned_item = item.strip().rstrip('*')
                    if cleaned_item:
                        description_parts.append(cleaned_item)
    # Join all parts with comma space
    description = ", ".join(description_parts)
    return description
