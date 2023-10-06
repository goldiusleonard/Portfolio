<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class EBookSeeder extends Seeder
{
    /**
     * Run the database seeds.
     *
     * @return void
     */
    public function run()
    {
        DB::table('e_books')->insert([
            [
                'title' => 'Do Androids Dream of Electric Sheep?',
                'author' => 'Philip K. Dick',
                'description' => 'One of the legendary media titles of all-time, Do Androids Dream of Electric Sheep? has a lot to do with androids and a little bit to do with electric sheep. It hints at one of the more pressing questions about robotics, though, which is the capacity for robots to think - Philip Dick was considering the issue in 1968. The book was the basis for the movie Blade Runner.'
            ],[
                'title' => 'Everything I Never Told You',
                'author' => 'Celeste Ng',
                'description' => 'If you were to see this Celeste Ng novel in a bookstore, you would probably think, “That is going to be a really sad story about someone dying.” And you would be right. The title grips a reader because they want to know what was not told and why it was not told. Everything I Never Told You is so much more than a sob story, though, and that is why it won countless awards back in 2014.'
            ],[
                'title' => 'Is Everyone Hanging Out Without Me? (and Other Concerns)',
                'author' => 'Mindy Kaling',
                'description' => 'Mindy Kaling gets right to the heart of the issue in this comedic autobiography. Let us be real: we all ask this question when we are laying in bed on a Friday night, curled up with a book. At least if we are reading Is Everyone Hanging Out Without Me? we will have Mindy by our side!'
            ],[
                'title' => 'The Electric Kool-Aid Acid Test',
                'author' => 'Tom Wolfe',
                'description' => 'The Electric Kool-Aid Acid Test screams cool, since nothing is cooler than Kool-Aid…and electricity. And LSD, especially in the 1960s. Tom Wolfes nonfiction story details the touring life and LSD use of a band. That is a pretty cool story to tell.'
            ],[
                'title' => 'Are You There, Vodka? It is Me, Chelsea',
                'author' => 'Chelsea Handler',
                'description' => 'Instead of looking for God, Chelsea Handler is looking for a drink in Are You There, Vodka? It is Me, Chelsea. It is funny and blatant, just like the comedian. The best-selling autobiography of essays helped to launch Handler into even greater fame.'
            ],[
                'title' => 'The Devil Wears Prada',
                'author' => 'Lauren Weisberger',
                'description' => 'Before it was a feature film (and soon-to-be Broadway musical), The Devil Wears Prada was a best-selling book. Lauren Weisbergers title sticks so well because of the imagery it invokes, with an illusion of a fiery being wearing Prada heels. We have probably all met someone like this, too…'
            ],[
                'title' => 'The Curious Incident of the Dog in the Night-Time',
                'author' => 'Mark Haddon',
                'description' => 'The Curious Incident of the Dog in the Night-Time is now a successful stage adaptation, but the title lacks some originality; it is actually a Sherlock Holmes quote from an Sir Arthur Conan Doyle short story. Mark Haddon applies it perfectly, however, to the story about a savant who is just a bit different than everyone else.'
            ],[
                'title' => 'How to Win Friends and Influence People',
                'author' => 'Dale Carnegie',
                'description' => 'One of the best selling self-help books of all-time, How to Win Friends and Influence People immediately gets to the point. Dale Carnegie wanted people to be influenced by his book about influencing people and a title about finding success was the perfect way to get peoples attention.'
            ],[
                'title' => 'Cloudy with a Chance of Meatballs',
                'author' => 'Judi Barrett',
                'description' => 'The classic childrens book uses a spectacular image to grab peoples attention: Could you imagine looking up in the sky and seeing meatballs beginning to rain down? That is the colorful image the equally colorful book creates with its title. Judi Barretts then-husband, Ron Barrett, helped the title come to life with some stunning illustrations.'
            ],[
                'title' => 'Love in the Time of Cholera',
                'author' => 'Gabriel García Márquez',
                'description' => 'Love in the Time of Cholera is one of the most respected books of all-time. It helps to have a title that raises the stakes before a reader even opens the novel. Gabriel Garcia Marquez notes “time” in his title, but the story has a tragic, timeless quality about it. You already know that a story of love during an epidemic that killed thousands will be heart-wrenching.'
            ],[
                'title' => 'The Princess Diarist',
                'author' => 'Carrie Fisher',
                'description' => 'In this hilarious and insightful memoir, the late Carrie Fisher relays to us what happened behind the scenes of Star Wars. Fisher compiles the diary entries she wrote at just 19 and gives readers a honest recollection of her young days on set.'
            ],[
                'title' => 'The Sellout',
                'author' => 'Paul Beatty',
                'description' => 'This Man Booker Prize winner is a funny yet tense satire about race in America. The narrator brings back segregation and slavery to his home neighborhood (he segregates the school, for example); what ensues is a challenging and unique side of the story that takes our narrator to the Supreme Court.'
            ],[
                'title' => 'The Secret History',
                'author' => 'Donna Tartt',
                'description' => 'Easily influenced by their exuberant professor, a group of students form a companionship with one another that will change their lives. When they go beyond what anyone thought they were capable of, they realize just how far gone they are and how easy it is to be immoral.'
            ],[
                'title' => '1984',
                'author' => 'George Orwell',
                'description' => 'This dystopian classic has been selling out recently. For some, it seems that Orwell has predicted the future. When Winston Smith notices that the Party has been watching him, he begins to fear for his life and the lives of everyone around him. Big Brother is always watching. Everywhere.'
            ],[
                'title' => 'The Husbands Secret',
                'author' => 'Liane Moriarty',
                'description' => 'Cecelia Fitzpatricks husband has written her a letter with intention for her to read it after her dies What her husband doesn’t know is that she stumbled across the letter while he is still alive. It contains his deepest, darkest secrets. What does the letter contain and how will Cecelia react?'
            ]
        ]);
    }
}
