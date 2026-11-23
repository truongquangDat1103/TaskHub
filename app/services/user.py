from app.models import User
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def update_profile(self, user: User, payload: UserUpdate) -> User:
        values = payload.model_dump(exclude_unset=True)
        if not values:
            return user
        return await self.user_repository.update(user, values)
