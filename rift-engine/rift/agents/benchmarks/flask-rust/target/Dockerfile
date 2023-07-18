# Use the official Rust image from the Docker Hub
FROM rust:1.52.1

# Set the working directory in the Docker image
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in Cargo.toml
RUN cargo install --path .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define the command to run your app using CMD which defines your runtime
CMD ["cargo", "run", "--bin", "app"]# Use the official Rust image from the Docker Hub
FROM rust:1.52.1

# Set the working directory in the Docker image
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in Cargo.toml
RUN cargo install --path .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define the command to run your app using CMD which defines your runtime
CMD ["cargo", "run", "--bin", "app"]