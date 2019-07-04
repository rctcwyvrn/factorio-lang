# factorio-lang

**Have you ever wanted to code by defining conveyor belts between concurrent by default factories?**  

Probably not. Especially not if the language is a buggy implementation in python. **BUT** if you have then **THIS** is the **LANGUAGE** for **YOU**!

**factorio-lang**:*the language so weird that I can trick you into thinking it's actually useful for a few minutes*
**Now that I have your expectations set low, here's the features of the language:**
1. Syntax is defining what goes in and what goes out of functions, in which port and out which ports
2. Because of #1, the language is concurrent by default, every factory "runs" indepentently from one another, and simply waits if there is no input
3. Support for importing python functions

**What can I use this for?**  
- Paralleizing (quickly but badly). Factorio-lang is a simple way to parallelize tasks, just write the complicated computation parts in python and use factorio-lang to manage the control flow
- Education. I think that this way of thinking about computer programs is useful for those who have 0 experience or have trouble with thinking about normal imperative languages.

**How do I use it?**  
1. Download the repo
2. Make sure you have python 3 installed
3. (TODO: Make command line arguments for file input) Change the name of the file at the bottom of factorpy.py to whatever you want to run.
4. Run it! Change the DEBUG constant at the top if you want to see what is happening internally

**What does ___ error mean?**  
I have no idea. Don't ask me lol.

**Why did you make this?**    
I had the idea one day and couldn't resist. Life's too short to not do stupid things for their own sake.

**Examples?**  
test.fl is going to be whatever I'm personally testing on my machine at that moment, so it shows to what syntax the current interpreter can execute. Examples.fl shows some ideas for what I eventually want to reach.

**I can't understand your spaghetti code, how does this monstrosity work?**  
See interpreter_doc.md and cmooon my code isn't thaaaaaaaaat bad.  


