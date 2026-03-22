"""
Permission system using 2-bit flags.

A Permission class wraps a permission ID and provides:
- Instance methods for checking the wrapped permission
- Class methods for checking arbitrary permission IDs

Permission bits:
- Bit 0: is_member
- Bit 1: is_admin (admin implies member)

Usage:
    >>> perm = Permission(3)  # ADMIN
    >>> perm.is_admin()
    True
    >>> perm.is_member()
    True
    >>> Permission.check_is_admin(3)
    True
"""

class Permission:
    """
    Wraps a permission ID and provides methods to check permissions.
    """
    
    # Permission bit flags
    _MEMBER_BIT = 0b01  # Bit 0
    _ADMIN_BIT = 0b10   # Bit 1
    
    # permission IDs
    NONE = 0
    MEMBER = 1
    ADMIN = 3
    
    def __init__(self, perm_id: int):
        """
        Initialize a Permission wrapper.
        
        :param perm_id: The permission ID (0-3)
        :raises ValueError: If perm_id is not in valid range
        """
        if perm_id < 0 or perm_id > 3:
            raise ValueError(f"Invalid permission ID: {perm_id}. Must be 0-3.")
        self.id = perm_id
    
    def is_admin(self) -> bool:
        """Check if this permission is admin."""
        return bool(self.id & self._ADMIN_BIT)
    
    def is_member(self) -> bool:
        """Check if this permission is member."""
        return bool(self.id & self._MEMBER_BIT)
    
    def has(self, required: int) -> bool:
        """
        Check if this permission satisfies the required permission.
        
        :param required: The required permission ID
        :return: True if this permission satisfies the requirement
        """
        # If this user is admin, they have all permissions
        if self.is_admin():
            return True
        
        # Otherwise check exact bit match
        return (self.id & required) == required
    
    def __eq__(self, other) -> bool:
        """Check equality with another Permission or int."""
        if isinstance(other, Permission):
            return self.id == other.id
        elif isinstance(other, int):
            return self.id == other
        return False

    def __str__(self) -> str:
        """Human-readable permission name."""
        if self.id == self.ADMIN:
            return "Admin"
        elif self.id == self.MEMBER:
            return "Member"
        elif self.id == self.NONE:
            return "None"
        else:
            return f"Unknown({self.id})"
    
    def __repr__(self) -> str:
        return f"Permission({self.id})"
    
    # Class methods for checking arbitrary permission IDs
    @classmethod
    def check_is_admin(cls, perm_id: int) -> bool:
        """Check if a permission ID is admin."""
        return bool(perm_id & cls._ADMIN_BIT)
    
    @classmethod
    def check_is_member(cls, perm_id: int) -> bool:
        """Check if a permission ID is member."""
        return bool(perm_id & cls._MEMBER_BIT)
    
    @classmethod
    def check_has(cls, perm_id: int, required: int) -> bool:
        """
        Check if a permission ID has the required permission.
        Admin implies member.
        
        :param perm_id: The permission ID to check
        :param required: The required permission level
        :return: True if the permission is satisfied
        """
        perm = cls(perm_id)
        return perm.has(required)
    
    @classmethod
    def to_string(cls, perm_id: int) -> str:
        """Convert a permission ID to a human-readable string."""
        return str(cls(perm_id))

PermissionMapping: dict[int, str] = {
    Permission.NONE: "無權限",
    Permission.MEMBER: "成員",
    Permission.ADMIN: "管理員"
}

