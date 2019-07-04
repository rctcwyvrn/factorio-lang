# factorio-lang

<span style="font-size:16em;">Have you ever wanted to code by defining conveyor belts between concurrent by default factories?</span>  

Probably not. Especially not if the language is a buggy implementation in python. *BUT* if you have then **THIS** is the *LANGUAGE* for **YOU**!

<span style="font-size:16em;">Now that I have your expectations set low, here's the features of the language:</span>
1. Syntax is defining what goes in and what goes out of functions, in which port and out which ports
2. Because of #1, the language is concurrent by default, every factory "runs" indepentently from one another, and simply waits if there is no input
3. Support for importing python functions

<span style="font-size:16em;">What can I use this for?</span>  
- Paralleizing (quickly but badly). Factorio-lang is a simple way to parallelize tasks, just write the complicated computation parts in python and use factorio-lang to manage the control flow
- Education. I think that this way of thinking about computer programs is useful for those who have 0 experience or have trouble with thinking about normal imperative languages.

<span style="font-size:16em;">How do I use it?</span>  
1. Download the repo
2. Make sure you have python 3 installed
3. (TODO: Make command line arguments for file input) Change the name of the file at the bottom of factorpy.py to whatever you want to run.
4. Run it! Change the DEBUG constant at the top if you want to see what is happening internally

<span style="font-size:16em;">What does ___ error mean?</span>  
I have no idea. Don't ask me lol.

<span style="font-size:16em;">Why did you make this?</span>    
I had the idea one day and couldn't resist. Life's too short to not do stupid things for their own sake.

<span style="font-size:16em;">Examples?</span>  
test.fl is going to be whatever I'm personally testing on my machine at that moment, so it shows to what syntax the current interpreter can execute. Examples.fl shows some ideas for what I eventually want to reach.

<span style="font-size:16em;">I can't understand your spaghetti code, how does this monstrosity work?</span>  
See interpreter_doc.md and cmooon my code isn't thaaaaaaaaat bad.  


