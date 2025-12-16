import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.models import User, Area
from ppgc_backend.app.controllers.hotels.models import Hotel, Room
from ppgc_backend.app.controllers.properties.models import Property
from ppgc_backend.app.controllers.auth.services import fetched_access_token
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.model_helper import CloudImageDetail


@pytest.mark.asyncio
async def test_rate_hotel_success(client__fixture):
    """Test successfully rating a hotel"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    # Create test user and hotel
    user = await create_test_user(test_db)
    manager = await create_test_user(test_db)

    area = Area(
        country='Test Country',
        state_or_province='Test State',
        city_or_town='Test City',
        street='123 Test St',
    )
    test_db.add(area)
    await test_db.flush()

    hotel = Hotel(
        name='Test Hotel',
        description='A test hotel',
        area_id=area.id,
        manager_id=manager.id,
        cover_image={'secure_url': 'https://example.com/hotel.jpg', 'public_id': 'hotel1'},
    )
    test_db.add(hotel)
    await test_db.commit()

    # Submit rating
    token = fetched_access_token(user)['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    payload = {
        'asset_type': 'hotel',
        'asset_id': hotel.id,
        'comment': 'Great hotel, nice rooms',
        'score': 5
    }

    resp = await http_client.post('/ratings', json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['comment'] == 'Great hotel, nice rooms'
    assert data['score'] == 5
    assert data['asset_type'] == 'hotel'
    assert data['asset_id'] == hotel.id


@pytest.mark.asyncio
async def test_rate_room_success(client__fixture):
    """Test successfully rating a room"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    # Create test user, hotel and room
    user = await create_test_user(test_db)
    manager = await create_test_user(test_db)

    area = Area(
        country='Test Country',
        state_or_province='Test State',
        city_or_town='Test City',
        street='123 Test St',
    )
    test_db.add(area)
    await test_db.flush()

    hotel = Hotel(
        name='Test Hotel',
        description='A test hotel',
        area_id=area.id,
        manager_id=manager.id,
        cover_image={'secure_url': 'https://example.com/hotel.jpg', 'public_id': 'hotel1'},
    )
    test_db.add(hotel)
    await test_db.flush()

    room = Room(
        room_type='single',
        room_number='101',
        price_per_night=100.0,
        max_occupancy=1,
        hotel_id=hotel.id,
        cover_image={'secure_url': 'https://example.com/room.jpg', 'public_id': 'room1'},
    )
    test_db.add(room)
    await test_db.commit()

    # Submit rating
    token = fetched_access_token(user)['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    payload = {
        'asset_type': 'room',
        'asset_id': room.id,
        'comment': 'Comfortable room, clean',
        'score': 4
    }

    resp = await http_client.post('/ratings', json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['comment'] == 'Comfortable room, clean'
    assert data['score'] == 4
    assert data['asset_type'] == 'room'
    assert data['asset_id'] == room.id


@pytest.mark.asyncio
async def test_rate_property_success(client__fixture):
    """Test successfully rating a property"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    # Create test user and property
    user = await create_test_user(test_db)

    area = Area(
        country='Test Country',
        state_or_province='Test State',
        city_or_town='Test City',
        street='123 Test St',
    )
    test_db.add(area)
    await test_db.flush()

    prop = Property(
        title='Test Property',
        price=100.0,
        description='A test property',
        availability='available',
        type='apartment',
        area_id=area.id,
    )
    test_db.add(prop)
    await test_db.commit()

    # Submit rating
    token = fetched_access_token(user)['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    payload = {
        'asset_type': 'property',
        'asset_id': prop.id,
        'comment': 'Nice property, good location',
        'score': 5
    }

    resp = await http_client.post('/ratings', json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data['comment'] == 'Nice property, good location'
    assert data['score'] == 5
    assert data['asset_type'] == 'property'
    assert data['asset_id'] == prop.id


@pytest.mark.asyncio
async def test_rating_invalid_asset_type(client__fixture):
    """Test rating with invalid asset type"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    user = await create_test_user(test_db)
    token = fetched_access_token(user)['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    payload = {
        'asset_type': 'invalid_type',
        'asset_id': 1,
        'comment': 'Test comment',
        'score': 5
    }

    resp = await http_client.post('/ratings', json=payload, headers=headers)
    assert resp.status_code == 400
    assert 'Invalid asset_type' in resp.json()['detail']


@pytest.mark.asyncio
async def test_rating_asset_not_found(client__fixture):
    """Test rating a non-existent asset"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    user = await create_test_user(test_db)
    token = fetched_access_token(user)['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    payload = {
        'asset_type': 'hotel',
        'asset_id': 999,
        'comment': 'Test comment',
        'score': 5
    }

    resp = await http_client.post('/ratings', json=payload, headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rating_invalid_score(client__fixture):
    """Test rating with invalid score (out of range)"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    user = await create_test_user(test_db)
    token = fetched_access_token(user)['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # Test score > 5
    payload = {
        'asset_type': 'hotel',
        'asset_id': 1,
        'comment': 'Test comment',
        'score': 10
    }

    resp = await http_client.post('/ratings', json=payload, headers=headers)
    assert resp.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_ratings_for_hotel(client__fixture):
    """Test retrieving all ratings for a hotel"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    # Create users, hotel and ratings
    user1 = await create_test_user(test_db)
    user2 = await create_test_user(test_db)
    manager = await create_test_user(test_db)

    area = Area(
        country='Test Country',
        state_or_province='Test State',
        city_or_town='Test City',
        street='123 Test St',
    )
    test_db.add(area)
    await test_db.flush()

    hotel = Hotel(
        name='Test Hotel',
        description='A test hotel',
        area_id=area.id,
        manager_id=manager.id,
        cover_image={'secure_url': 'https://example.com/hotel.jpg', 'public_id': 'hotel1'},
    )
    test_db.add(hotel)
    await test_db.commit()

    # Submit two ratings
    token1 = fetched_access_token(user1)['access_token']
    headers1 = {'Authorization': f'Bearer {token1}'}

    payload1 = {
        'asset_type': 'hotel',
        'asset_id': hotel.id,
        'comment': 'Great hotel',
        'score': 5
    }
    await http_client.post('/ratings', json=payload1, headers=headers1)

    token2 = fetched_access_token(user2)['access_token']
    headers2 = {'Authorization': f'Bearer {token2}'}

    payload2 = {
        'asset_type': 'hotel',
        'asset_id': hotel.id,
        'comment': 'Good hotel',
        'score': 4
    }
    await http_client.post('/ratings', json=payload2, headers=headers2)

    # Get ratings
    resp = await http_client.get(f'/ratings/hotel/{hotel.id}')
    assert resp.status_code == 200
    data = resp.json()
    assert data['total'] == 2
    assert data['average_score'] == 4.5
    assert len(data['ratings']) == 2


@pytest.mark.asyncio
async def test_delete_own_rating(client__fixture):
    """Test deleting own rating"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    user = await create_test_user(test_db)
    manager = await create_test_user(test_db)

    area = Area(
        country='Test Country',
        state_or_province='Test State',
        city_or_town='Test City',
        street='123 Test St',
    )
    test_db.add(area)
    await test_db.flush()

    hotel = Hotel(
        name='Test Hotel',
        description='A test hotel',
        area_id=area.id,
        manager_id=manager.id,
        cover_image={'secure_url': 'https://example.com/hotel.jpg', 'public_id': 'hotel1'},
    )
    test_db.add(hotel)
    await test_db.commit()

    # Submit rating
    token = fetched_access_token(user)['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    payload = {
        'asset_type': 'hotel',
        'asset_id': hotel.id,
        'comment': 'Great hotel',
        'score': 5
    }

    create_resp = await http_client.post('/ratings', json=payload, headers=headers)
    rating_id = create_resp.json()['id']

    # Delete rating
    delete_resp = await http_client.delete(f'/ratings/{rating_id}', headers=headers)
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_cannot_delete_others_rating(client__fixture):
    """Test that a user cannot delete another user's rating"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    user1 = await create_test_user(test_db)
    user2 = await create_test_user(test_db)
    manager = await create_test_user(test_db)

    area = Area(
        country='Test Country',
        state_or_province='Test State',
        city_or_town='Test City',
        street='123 Test St',
    )
    test_db.add(area)
    await test_db.flush()

    hotel = Hotel(
        name='Test Hotel',
        description='A test hotel',
        area_id=area.id,
        manager_id=manager.id,
        cover_image={'secure_url': 'https://example.com/hotel.jpg', 'public_id': 'hotel1'},
    )
    test_db.add(hotel)
    await test_db.commit()

    # User1 submits rating
    token1 = fetched_access_token(user1)['access_token']
    headers1 = {'Authorization': f'Bearer {token1}'}

    payload = {
        'asset_type': 'hotel',
        'asset_id': hotel.id,
        'comment': 'Great hotel',
        'score': 5
    }

    create_resp = await http_client.post('/ratings', json=payload, headers=headers1)
    rating_id = create_resp.json()['id']

    # User2 tries to delete user1's rating
    token2 = fetched_access_token(user2)['access_token']
    headers2 = {'Authorization': f'Bearer {token2}'}

    delete_resp = await http_client.delete(f'/ratings/{rating_id}', headers=headers2)
    assert delete_resp.status_code == 403


@pytest.mark.asyncio
async def test_rating_updates_hotel_aggregates(client__fixture):
    """Test that rating a hotel updates its total_ratings and total_stars"""
    test_db: AsyncSession = client__fixture['db']
    http_client: AsyncClient = client__fixture['http_client']

    user = await create_test_user(test_db)
    manager = await create_test_user(test_db)

    area = Area(
        country='Test Country',
        state_or_province='Test State',
        city_or_town='Test City',
        street='123 Test St',
    )
    test_db.add(area)
    await test_db.flush()

    hotel = Hotel(
        name='Test Hotel',
        description='A test hotel',
        area_id=area.id,
        manager_id=manager.id,
        cover_image={'secure_url': 'https://example.com/hotel.jpg', 'public_id': 'hotel1'},
        total_ratings=0,
        total_stars=0,
    )
    test_db.add(hotel)
    await test_db.commit()

    # Submit rating
    token = fetched_access_token(user)['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    payload = {
        'asset_type': 'hotel',
        'asset_id': hotel.id,
        'comment': 'Great hotel',
        'score': 4
    }

    await http_client.post('/ratings', json=payload, headers=headers)

    # Verify hotel aggregates updated
    await test_db.refresh(hotel)
    assert hotel.total_ratings == 1
    assert hotel.total_stars == 4
