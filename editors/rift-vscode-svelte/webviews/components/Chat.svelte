<!-- Navbar.svelte -->
<script>
    import { onMount } from 'svelte';
    let activeItem = 'Home';
  
    function handleClick(item) {
      activeItem = item;
    }
  </script>
  
  <style>

  </style>
  
  <div class="flex flex-row">
    <div><button class="bg-red-500" on:click={() => handleClick('Home')} class:active={activeItem === 'Home'}>Home</button></div>
    <div><button class="navbar-item" on:click={() => handleClick('About')} class:active={activeItem === 'About'}>About</button></div>
    <div><button class="navbar-item" on:click={() => handleClick('Contact')} class:active={activeItem === 'Contact'}>Contact</button></div>
  </div>