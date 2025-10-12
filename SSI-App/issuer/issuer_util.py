from urllib.parse import urlparse, parse_qs

def extract_raw_invitation(invitation_url: str) -> str:
    """
    Parses a URL to extract the value of the '_oob' query parameter.

    Args:
        invitation_url: The full invitation URL containing the _oob parameter.

    Returns:
        The raw, Base64-encoded invitation string.

    Raises:
        ValueError: If the '_oob' parameter is not found in the URL.
    """
    # Parse the URL into its components (scheme, path, query, etc.)
    parsed_url = urlparse(invitation_url)
    
    # Parse the query string into a dictionary
    # Note: parse_qs returns a dictionary where values are lists
    query_params = parse_qs(parsed_url.query)
    
    # Get the list of values for the '_oob' key
    raw_invitation_list = query_params.get('_oob')
    
    # Check if the parameter exists and has a value
    if not raw_invitation_list:
        raise ValueError("'_oob' parameter not found in the URL.")
        
    # Return the first value from the list
    return raw_invitation_list[0]