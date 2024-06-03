import pygame
import random
import queue

# Define constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CUSTOMER_SIZE = (50, 50)
CASHIER_SIZE = (50, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CUSTOMER_SPEED = 2

EXIT_POSITION = (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50)  # Exit position at the bottom right

class Customer:
    def __init__(self, arrival_time, items):
        self.arrival_time = arrival_time
        self.items = items
        self.position = (random.randint(0, SCREEN_WIDTH - CUSTOMER_SIZE[0]), 0)  # Start at a random position at the top
        self.target_position = None
        self.exiting = False
        self.service_start_time = None
        self.departure_time = None

    def move_towards(self, target):
        x, y = self.position
        target_x, target_y = target
        if x < target_x:
            x = min(x + CUSTOMER_SPEED, target_x)
        elif x > target_x:
            x = max(x - CUSTOMER_SPEED, target_x)
        if y < target_y:
            y = min(y + CUSTOMER_SPEED, target_y)
        elif y > target_y:
            y = max(y - CUSTOMER_SPEED, target_y)
        self.position = (x, y)

class Cashier:
    def __init__(self, position):
        self.current_customer = None
        self.time_remaining = 0
        self.position = position
        self.queue = queue.Queue()
        self.customers_served = 0

    def tick(self, current_time):
        if self.current_customer is not None:
            self.time_remaining -= 1
            if self.time_remaining <= 0:
                self.current_customer.exiting = True
                self.current_customer.departure_time = current_time
                self.current_customer = None
                self.customers_served += 1
        if self.current_customer is None and not self.queue.empty():
            self.start_next(self.queue.get(), current_time)

    def is_busy(self):
        return self.current_customer is not None

    def start_next(self, new_customer, current_time):
        self.current_customer = new_customer
        new_customer.service_start_time = current_time
        # Calculate time needed to serve the customer based on the number of items
        min_time = 1.5 * 60  # Minimum 1.5 seconds in terms of simulation time
        max_time = 3.0 * 60  # Maximum 3.0 seconds in terms of simulation time
        self.time_remaining = int(min_time + (max_time - min_time) * (new_customer.items / 50))
        new_customer.target_position = (self.position[0] + CASHIER_SIZE[0], self.position[1])

def simulate(supermarket_opening_time, total_customers, cashier_count):
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Simulasi Antrean Superindo")
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()

    # Load images
    customer_img = pygame.transform.scale(pygame.image.load("customer.png"), CUSTOMER_SIZE)
    cashier_img = pygame.transform.scale(pygame.image.load("cashier.png"), CASHIER_SIZE)

    # Initialize the simulation variables
    customers = queue.Queue()
    cashiers = [Cashier((100 + i * 150, SCREEN_HEIGHT - 100)) for i in range(cashier_count)]
    waiting_times = []
    served_customers = 0
    all_customers = []
    completed_customers = []  # List to store customers who have completed service

    # Generate customers with staggered arrivals
    arrival_interval = 60  # Interval between arrivals (in frames)
    current_arrival_time = 0
    for _ in range(total_customers):
        arrival_time = random.randint(current_arrival_time, current_arrival_time + arrival_interval)
        current_arrival_time = arrival_time
        items = random.randint(1, 50)  # Assume each customer buys between 1 and 50 items
        customer = Customer(arrival_time, items)
        customers.put(customer)
        all_customers.append(customer)

    # Run the simulation
    current_time = 0
    running = True
    while running and (current_time < supermarket_opening_time or not customers.empty() or any(cashier.is_busy() for cashier in cashiers) or completed_customers):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(WHITE)

        # Move customers towards their target positions (queues)
        for customer in all_customers:
            if customer.arrival_time <= current_time:  # Only move customers who have arrived
                if not customer.exiting:  # Move only if not exiting
                    if customer.target_position:
                        customer.move_towards(customer.target_position)
                        screen.blit(customer_img, customer.position)

        # Process new arrivals
        while not customers.empty() and customers.queue[0].arrival_time <= current_time:
            customer = customers.get()
            shortest_queue = min(cashiers, key=lambda cashier: cashier.queue.qsize())
            shortest_queue.queue.put(customer)
            customer.target_position = (shortest_queue.position[0] + CUSTOMER_SIZE[0], shortest_queue.position[1])

        # Update cashier status and draw queues
        total_customers_waiting = sum(cashier.queue.qsize() for cashier in cashiers)

        for cashier in cashiers:
            cashier.tick(current_time)
            screen.blit(cashier_img, cashier.position)

            # Draw current customer
            if cashier.current_customer:
                screen.blit(customer_img, cashier.current_customer.position)

            # Draw queue
            for i, customer in enumerate(list(cashier.queue.queue)):
                target_pos = (cashier.position[0] + CUSTOMER_SIZE[0], cashier.position[1] - (i + 1) * CUSTOMER_SIZE[1])
                customer.target_position = target_pos
                screen.blit(customer_img, customer.position)

        # Move completed customers from cashiers to exit
        for cashier in cashiers:
            if cashier.current_customer and cashier.current_customer.exiting:
                if cashier.current_customer.position != cashier.position:  # Check if customer is not near the cashier
                    # Move customer back to the cashier
                    target_pos = (cashier.position[0] + CUSTOMER_SIZE[0], cashier.position[1])
                    cashier.current_customer.target_position = target_pos
                else:
                    # Move customer towards exit
                    cashier.current_customer.move_towards(EXIT_POSITION)
                screen.blit(customer_img, cashier.current_customer.position)
                if cashier.current_customer.position == EXIT_POSITION:
                    completed_customers.append(cashier.current_customer)
                    cashier.current_customer = None

        # Move completed customers to the exit
        for customer in completed_customers:
            customer.move_towards(EXIT_POSITION)
            screen.blit(customer_img, customer.position)

        # Check if completed customers have reached the
        # exit and remove them
        completed_customers =[customer for customer in completed_customers if customer.position != EXIT_POSITION]

        # Calculate waiting times for customers who have departed
        for customer in all_customers:
            if customer.departure_time is not None:
                waiting_time = customer.departure_time - customer.arrival_time
                waiting_times.append(waiting_time)
                all_customers.remove(customer)
                completed_customers.append(customer)  # Move completed customers to the list

        # Update statistics
        served_customers = sum(cashier.customers_served for cashier in cashiers)
        if waiting_times:
            average_waiting_time = sum(waiting_times) / len(waiting_times) / 60  # Convert frames to seconds
        else:
            average_waiting_time = 0

        # Display stats
        total_customers_text = font.render(f'Total Customers: {total_customers}', True, BLACK)
        served_customers_text = font.render(f'Served Customers: {served_customers}', True, BLACK)
        avg_waiting_time_text = font.render(f'Avg Waiting Time: {average_waiting_time:.2f} sec', True, BLACK)
        total_customers_waiting_text = font.render(f'Waiting Customers: {total_customers_waiting}', True, BLACK)

        screen.blit(total_customers_text, (10, 10))
        screen.blit(served_customers_text, (10, 50))
        screen.blit(avg_waiting_time_text, (10, 90))
        screen.blit(total_customers_waiting_text, (10, 130))

        pygame.display.flip()
        clock.tick(60)  # Increase tick rate for smoother animation
        current_time += 1

    pygame.quit()

def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Supermarket Simulation - Main Menu")
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()

    menu_options = ["Hari Biasa", "Hari Libur", "Awal Bulan"]
    config = {
        'Hari Biasa': {'total_customers': 100, 'cashier_count': 3},
        'Hari Libur': {'total_customers': 150, 'cashier_count': 4},
        'Awal Bulan': {'total_customers': 200, 'cashier_count': 5}
    }
    selected_option = 0

    while True:
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    selected_day = menu_options[selected_option]
                    supermarket_opening_time = 3600  # Simulasi selama 1 jam dalam detik
                    simulate(supermarket_opening_time, config[selected_day]['total_customers'], config[selected_day]['cashier_count'])
                    return

        for i, option in enumerate(menu_options):
            color = BLACK
            if i == selected_option:
                color = (0, 0, 255)
            text = font.render(option, True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2 + i * 40))

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main_menu()
