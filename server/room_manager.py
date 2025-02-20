# room_manager.py (Pass connected_clients and corrected participant counting)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, not_
from sqlalchemy.orm import joinedload
from server.models import Room, User, room_participants
from datetime import datetime, timezone
import logging
from typing import Optional, List  # Import List

logger = logging.getLogger(__name__)

async def get_room(db_session: AsyncSession, room_id: int) -> Optional[Room]:
    """Retrieves a room by its ID."""
    result = await db_session.execute(select(Room).where(Room.id == room_id))
    return result.scalars().first()

async def find_available_room(db_session: AsyncSession) -> Optional[Room]:
    """Finds an available room (status 'waiting', and not a guest room)."""
    logger.debug("find_available_room: called")
    try:
        stmt = select(Room).where(Room.status == 'waiting').where(not_(Room.game_state.has_key("guest_room")))
        logger.debug(f"find_available_room: generated SQL: {stmt.compile(compile_kwargs={'literal_binds': True})}")
        result = await db_session.execute(stmt)
        room = result.scalars().first()
        logger.debug(f"find_available_room: found room: {room}")
        return room
    except Exception as e:
        logger.exception("find_available_room: Exception occurred")
        raise


async def find_available_guest_room(db_session: AsyncSession, connected_clients: List) -> Optional[Room]: # Added connected_clients
    """Finds an available room specifically for guest users, considering occupancy."""
    logger.debug("find_available_guest_room: called")
    try:
        # Find waiting rooms marked as guest rooms
        result = await db_session.execute(
            select(Room)
            .where(Room.status == 'waiting')
            .where(Room.game_state.has_key("guest_room"))
            .options(joinedload(Room.participants))  # Eager load participants
        )
        rooms = result.unique().scalars().all()  # Fetch all matching rooms, ensuring uniqueness
        logger.debug(f"find_available_guest_room: found rooms: {rooms}")

        # Find a room with less than 2 participants
        for room in rooms:
            # Count connected clients for this room -- Using passed in list
            connected_count = sum(1 for client in connected_clients if client.room_id == room.id and client.is_active)
            logger.debug(f"find_available_guest_room: room {room.id}, connected_count: {connected_count}")

            if connected_count < 2:
                logger.debug(f"find_available_guest_room: returning available room: {room.id}")
                return room

        # If no available guest room, return None
        logger.debug("find_available_guest_room: no available room found, returning None")
        return None

    except Exception as e:
        logger.exception("find_available_guest_room: Exception occurred")
        raise

async def add_participant(db_session: AsyncSession, room: Room, user: User, role: str):
    """Add a participant to a room.  Handles guests by skipping the insert."""
    if not user.is_guest:  # Only add to room_participants if NOT a guest
        try:
            await db_session.execute(
                room_participants.insert().values(
                    user_id=user.id,
                    room_id=room.id,
                    role=role
                )
            )
            await db_session.commit()
            logger.info(f"Added participant {user.id} to room {room.id}")
        except Exception as e:
            logger.error(f"Error adding participant: {e}")
            await db_session.rollback()
            raise
    else:
        logger.info(f"Skipping add_participant for guest user in room {room.id}")


async def join_or_reconnect(db_session: AsyncSession, user: User, connected_clients: List) -> Optional[Room]: #Added connected_clients
    """Joins a user to a room or reconnects them, separating guests."""
    logger.info(f"Join/reconnect session ID: {id(db_session)}")
    logger.info(f"Session status: {'open' if db_session.is_active else 'closed'}")
    logger.info(f"User ID: {user.id}, is_guest: {user.is_guest}")

    try:
        # --- Reconnection Logic (for registered users) ---
        if not user.is_guest:
            logger.info("Checking for existing active rooms...")
            result = await db_session.execute(
                select(Room)
                .join(room_participants)
                .where(room_participants.c.user_id == user.id)
                .where(Room.status == 'active')
                .options(joinedload(Room.participants))
            )
            rooms = result.scalars().all()
            if rooms:
                last_room = rooms[-1]
                logger.info(f"Reconnecting user {user.id} to room {last_room.id}")
                return last_room

        # --- Guest vs. Registered Logic ---
        if user.is_guest:
            room = await find_available_guest_room(db_session, connected_clients) # Pass connected_clients
        else:
            room = await find_available_room(db_session)

        if room:
            logger.info(f"Found available room {room.id} for user {user.id}")
        else:
            if user.is_guest:
                room = Room(status='waiting', created_at=datetime.now(timezone.utc), game_state={"guest_room": True})
            else:
                room = Room(status='waiting', created_at=datetime.now(timezone.utc))
            db_session.add(room)
            await db_session.commit()
            await db_session.refresh(room)
            logger.info(f"Created new room {room.id} for user {user.id}")

        await db_session.refresh(room, ['participants'])
        # Use connected_clients to determine role for *both* guests and registered users.
        connected_count = sum(1 for client in connected_clients if client.room_id == room.id and client.is_active)
        logger.info(f"Room: {room.id}, Connected Clients (for role assignment): {connected_count}")
        role = "candidate" if connected_count % 2 == 0 else "hr"

        # --- Guest User Handling (don't check for existing participation) ---
        if not user.is_guest:
            existing_participant = await db_session.execute(
                select(room_participants)
                .where(room_participants.c.user_id == user.id)
                .where(room_participants.c.room_id == room.id)
            )
            if existing_participant.scalar():
                logger.info(f"User {user.id} already in room {room.id}")
                return room

        # Add the participant (call the modified add_participant)
        await add_participant(db_session, room, user, role)
        logger.info(f"After adding participant - Session active: {db_session.is_active}")

        return room

    except Exception as e:
        logger.error(f"Error in join_or_reconnect: {str(e)}")
        raise

async def handle_disconnect(db_session: AsyncSession, user: User):
    """Handles user disconnection (updates last_seen)."""
    # Only update last_seen for registered users
    if not user.is_guest:
        result = await db_session.execute(select(User).where(User.id == user.id))
        user_db = result.scalars().first()

        if user_db:
          user_db.last_seen = datetime.now(timezone.utc)
          await db_session.commit()
          logger.info(f"User {user.id} disconnected, last_seen updated.")
        else:
            logger.warning(f"User not found on disconnect: {user.id}")