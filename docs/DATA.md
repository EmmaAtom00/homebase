## Entity-relationship diagram

```mermaid
erDiagram
    USER {
        int id  PK
        string  email   UK
        string  first_name
        string  last_name
        string  password_hash
        string  role
        boolean is_verified
        datetime    created_at
        datetime    updated_at
    }

    PROPERTY {
        int id  PK
        int user_id FK
        string  title
        string  description
        string  address
        string  slug
        decimal price
        datetime    created_at
        datetime    updated_at
    }

    BOOKING {
        int id  PK
        int user_id FK
        int property_id FK
        string  status
        date    check_in
        date    check_out
        decimal price
        datetime    created_at
    }

    REVIEW {

    }

    PAYMENT {

    }

    NOTIFICATION {

    }

    USER || --o{ PROPERTY : owns
    USER || --o{ BOOKING: makes
    PROPERTY || --o{ BOOKING: receives
    USER || --o{ REVIEW: writes
    BOOKING || --o{ PAYMENT: has
    USER || --o{ NOTIFICATION: receives
    BOOKING || --o{ REVIEW: has
```

## State diagram
```mermaid
stateDiagram
    direction LR

    [*] --> Requested

    Requested --> Approved
    Requested --> Declined
    Requested --> Canceled

    Approved --> Confirmed: Payment received
    Approved --> Expired: 24 hours without payment
    Approved --> Canceled

    Confirmed --> Completed: Stay is over
    Confirmed --> Canceled
```

### Notes/Constraints
1. Statuses that block the dates, so nobody else can book them.
    - Approved
    - Requested
    - Confirmed
    - Completed
2. There can oly be one review per booking
3. Why the booking stores the total price instead of working it out from the property's price each time is because: The landlord may change the price later, but the guest agreed to the old one.