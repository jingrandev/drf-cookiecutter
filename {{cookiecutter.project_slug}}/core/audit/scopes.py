class ScopeBuilder:
    @staticmethod
    def root() -> str:
        return "root"

    @staticmethod
    def object(scope_type: str, scope_id: int | str) -> str:
        return f"{scope_type}:{scope_id}"

    @staticmethod
    def user(user_id: int | str) -> str:
        return f"user:{user_id}"

    @staticmethod
    def custom(*parts: str) -> str:
        return ":".join(str(p) for p in parts)
