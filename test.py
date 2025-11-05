import requests
import json
import time

# Base URLs for your services
AUTH_SERVICE = "http://localhost:8001"
USER_SERVICE = "http://localhost:8004"
PRODUCT_SERVICE = "http://localhost:8002"


def get_browser_headers():
    """Return headers that mimic a browser request to trigger session creation"""
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Origin': 'http://localhost:3000',
        'Referer': 'http://localhost:3000/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'X-Requested-With': 'XMLHttpRequest'
    }


def test_session_sharing():
    print("🧪 Testing Session Sharing Across Microservices")
    print("=" * 50)

    # Use a session to maintain cookies across requests
    session = requests.Session()
    browser_headers = get_browser_headers()

    # Step 1: Create a guest session by accessing product service WITH BROWSER HEADERS
    print("\n1. Creating guest session via product service...")
    response = session.get(
        f"{PRODUCT_SERVICE}/api/v1/products/",
        headers=browser_headers
    )
    session_id_from_header = response.headers.get('X-Secure-Session-ID')
    session_id_from_cookie = session.cookies.get('session_id')

    print(f"   Response Status: {response.status_code}")
    print(f"   Session ID from Header: {session_id_from_header}")
    print(f"   Session ID from Cookie: {session_id_from_cookie}")

    if session_id_from_header:
        print("   ✅ Session created successfully!")
    else:
        print("   ❌ No session created - checking response headers:")
        for header, value in response.headers.items():
            if 'session' in header.lower() or 'cookie' in header.lower():
                print(f"      {header}: {value}")

    # Step 2: Verify the same session is used in user service
    print("\n2. Accessing user service with same session...")
    response = session.get(
        f"{USER_SERVICE}/api/v1/users/cart",
        headers=browser_headers
    )
    user_session_id = response.headers.get('X-Secure-Session-ID')

    print(f"   Response Status: {response.status_code}")
    print(f"   Session ID from User Service: {user_session_id}")
    print(f"   Session IDs Match: {session_id_from_header == user_session_id}")

    # Step 3: Add item to cart via user service
    if session_id_from_header:
        print("\n3. Adding item to cart via user service...")
        cart_data = {
            "product_id": 1,
            "quantity": 2
        }
        response = session.post(
            f"{USER_SERVICE}/api/v1/users/cart/1",
            json=cart_data,
            headers=browser_headers
        )
        print(f"   Add to Cart Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Item added to cart successfully")
            cart_response = response.json()
            print(f"   Session Based: {cart_response.get('session_based', 'Unknown')}")

    # Step 4: Verify cart via product service with same session
    print("\n4. Verifying cart via product service...")
    response = session.get(
        f"{PRODUCT_SERVICE}/api/v1/products/",
        headers=browser_headers
    )
    print(f"   Response Status: {response.status_code}")

    # Step 5: Test auth service session recognition
    print("\n5. Testing auth service session recognition...")
    response = session.get(
        f"{AUTH_SERVICE}/health",
        headers=browser_headers
    )
    auth_session_id = response.headers.get('X-Secure-Session-ID')
    print(f"   Auth Service Session ID: {auth_session_id}")

    # Step 6: Get session info from user service
    if session_id_from_header:
        print("\n6. Getting session info from user service...")
        response = session.get(
            f"{USER_SERVICE}/api/v1/users/session/info",
            headers=browser_headers
        )
        if response.status_code == 200:
            session_info = response.json()
            print(f"   Session Type: {session_info.get('session_type')}")
            print(f"   Cart Items Count: {session_info.get('cart_items_count')}")
            print(f"   User ID: {session_info.get('user_id')}")
        else:
            print(f"   Failed to get session info: {response.status_code}")

    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY:")

    if session_id_from_header and session_id_from_header == user_session_id == auth_session_id:
        print("✅ SUCCESS: Sessions are properly shared across all services!")
        print(f"   Shared Session ID: {session_id_from_header}")
    else:
        print("❌ Sessions are not properly shared or created")
        if not session_id_from_header:
            print("   ❌ No session was created in the first place")
        else:
            print(f"   Product Session: {session_id_from_header}")
            print(f"   User Session: {user_session_id}")
            print(f"   Auth Session: {auth_session_id}")


def test_with_curl_equivalent():
    """Test using the same approach that works with curl"""
    print("\n\n🔧 Testing with curl-equivalent approach")
    print("=" * 50)

    session = requests.Session()

    # Headers that definitely trigger session creation
    trigger_headers = {
        'Origin': 'http://localhost:3000',
        'Referer': 'http://localhost:3000/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'X-Requested-With': 'XMLHttpRequest'
    }

    print("1. Testing with session-triggering headers...")
    response = session.get(
        f"{PRODUCT_SERVICE}/api/v1/products/",
        headers=trigger_headers
    )

    session_id = response.headers.get('X-Secure-Session-ID')
    print(f"   Session ID: {session_id}")
    print(f"   Set-Cookie Headers: {[h for h in response.headers.get('set-cookie', '').split(',')]}")

    if session_id:
        print("   ✅ Session created with proper headers!")

        # Test session persistence
        print("\n2. Testing session persistence...")
        response2 = session.get(
            f"{USER_SERVICE}/api/v1/users/cart",
            headers=trigger_headers
        )
        session_id2 = response2.headers.get('X-Secure-Session-ID')
        print(f"   Same session maintained: {session_id == session_id2}")


if __name__ == "__main__":
    test_session_sharing()
    test_with_curl_equivalent()