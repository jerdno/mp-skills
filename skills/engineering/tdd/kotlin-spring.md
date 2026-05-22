# Kotlin + Spring Reference

Tech-stack specifics for [SKILL.md](SKILL.md). General rules (naming, mocking boundaries) live in [tests.md](tests.md) and [mocking.md](mocking.md).

## Stack
- JUnit 5, AssertJ
- SpringMockk (`@MockkBean`, `@SpykBean`)
- Testcontainers (Postgres/Kafka — not H2)
- Backtick test names following [tests.md](tests.md) convention

## Which test type
- **Service/component** — plain unit test, mock collaborators with MockK, no Spring context
- **Endpoint integration** — `@SpringBootTest` + Testcontainers, mock only external deps (HTTP clients, SDKs, brokers)
- **Repository** — `@DataJpaTest` only for custom queries; skip built-in Spring Data methods (`findById`, `save`, etc.)

Don't use `@SpringBootTest` for a single service — unit-test it instead.

## Unit test
```kotlin
class CheckoutServiceTest {
    private val paymentClient = mockk<PaymentClient>()
    private val checkout = CheckoutService(paymentClient)

    @Test
    fun `Order is confirmed when payment succeeds`() {
        every { paymentClient.charge(any()) } returns PaymentResult.Success("tx-123")
        assertThat(checkout.process(cart).status).isEqualTo(CONFIRMED)
    }
}
```

## Endpoint integration test
```kotlin
@SpringBootTest
@Testcontainers
class CheckoutEndpointTest {
    @Container val postgres = PostgreSQLContainer("postgres:16")
    @MockkBean lateinit var paymentClient: PaymentClient  // external only — never @MockkBean own services
    @Autowired lateinit var rest: TestRestTemplate
}
```
Verify through HTTP response, not raw `SELECT`.

## Assertions
- `assertAll` — multi-field checks on **one** outcome, not unrelated outcomes
- `usingRecursiveComparison().ignoringFields(...)` — whole-DTO equality, preferred over `assertAll` for DTO comparisons

```kotlin
assertAll(
    { assertThat(customer.email).isEqualTo("alice@example.com") },
    { assertThat(customer.tier).isEqualTo(STANDARD) },
)

assertThat(response.body)
    .usingRecursiveComparison()
    .ignoringFields("createdAt", "id")
    .isEqualTo(expected)
```
