# factorio-lang

**Have you ever wanted to code by defining conveyor belts between concurrent by default factories?**  

Probably not. Especially not if the language is a buggy implementation in python. **BUT** if you have then **THIS** is the **LANGUAGE** for **YOU**!

### factorio-lang, *the language so weird that I can trick you into thinking it's actually useful for a few minutes* ###  


**Now that I have your expectations set low, here's the features of the language:**
1. The code you write is defining what goes in and what goes out of functions. For example, A() -> B() means that B is waiting for inputs from A, and whatever A outputs will be passed into B.
2. Because of #1, the language is concurrent by default, every factory "runs" indepentently from one another, and simply waits if there is no input
3. Support for importing python functions, so you can import functions and have them act as factories. This lets you write some more difficult code in python and use them as parts within your factory

**What can I use this for?**  
- Paralleizing quickly but badly. Factorio-lang is a simple way to parallelize tasks, letting you write the complicated computation parts in python and use factorio-lang to manage the control/data flow
- Education. I think that this way of thinking about computer programs is useful for those who have 0 experience or have trouble with thinking about normal imperative languages. I plan to write some basic tutorials in factorio-lang as well as a GUI + visualizer to teach factorio-lang. More details in teaching.md

**How do I use it?**  
1. Download the repo
2. Make sure you have python 3 installed
3. (TODO: Make command line arguments for file input) Change the name of the file at the bottom of factorpy.py to whatever you want to run.
4. Run it! Change the DEBUG and DETAILED_DEBUG constants at the top if you want to see what is happening internally. DETAILED_DEBUG will show you what is happening before execution, DEBUG will show what is happening during execution.

**What does ___ error mean?**  
I have no idea. Don't ask me lol.

**Why did you make this?**    
I had the idea one day and couldn't resist. Life's too short to not do stupid things for their own sake.

**Examples?**  
test.fl and similarity named files are going to be whatever I'm personally testing on my machine at that moment, so it shows to what syntax the current interpreter can execute. Examples.fl shows some ideas for what I eventually want to reach.

**I can't understand your spaghetti code, how does this monstrosity work?**  
See interpreter_doc.md and cmooon my code isn't thaaaaaaaaat bad. EDIT: it's pretty bad


