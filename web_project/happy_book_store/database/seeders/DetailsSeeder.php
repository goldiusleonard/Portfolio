<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class DetailsSeeder extends Seeder
{
    /**
     * Run the database seeds.
     *
     * @return void
     */
    public function run()
    {
        DB::table('details')->insert([[
            'books_id' => 1,
            'author' => 'John Maxwell',
            'publisher' => 'Kompas Arahmana',
            'year' => 2019,
            'description' => 'This book is really great!',
        ],[
            'books_id' => 2,
            'author' => 'Rick Roll',
            'publisher' => 'Kompas Arahbarat',
            'year' => 2003,
            'description' => 'This book has an endless knowledge!',
        ],[
            'books_id' => 3,
            'author' => 'Watson Boston',
            'publisher' => 'Kompas Arahtimur',
            'year' => 2017,
            'description' => 'It \' a recommended book after all!!',
        ],[
            'books_id' => 4,
            'author' => 'Bambang Susan',
            'publisher' => 'Kompas Tidakberarah',
            'year' => 2020,
            'description' => 'You will never get bored reading this book!',
        ],[
            'books_id' => 5,
            'author' => 'Helen Mayor',
            'publisher' => 'Kompas Kemana',
            'year' => 2015,
            'description' => 'The best book ever to read!',
        ],[
            'books_id' => 6,
            'author' => 'Madison Gracia',
            'publisher' => 'Gemoidia',
            'year' => 2012,
            'description' => 'The Best seller book in its category!',
        ],[
            'books_id' => 7,
            'author' => 'Parto Ka Seto',
            'publisher' => 'Triniti Books',
            'year' => 2018,
            'description' => 'Most Recommended Book Ever!',
        ],[
            'books_id' => 8,
            'author' => 'Belvin Tannaka',
            'publisher' => 'Kompas Gemoidia',
            'year' => 2014,
            'description' => 'The best book for beginners!',
        ],[
            'books_id' => 9,
            'author' => 'Catherine Patricia',
            'publisher' => 'Kompas Arahkiri',
            'year' => 2016,
            'description' => 'This is a must read book!',
        ],[
            'books_id' => 10,
            'author' => 'Papa Zola',
            'publisher' => 'Koran Boboi',
            'year' => 2021,
            'description' => 'No book is like this before!',
        ],[
            'books_id' => 11,
            'author' => 'John Wick',
            'publisher' => 'Kompas Mana',
            'year' => 2017,
            'description' => 'You have to read this book!',
        ],[
            'books_id' => 12,
            'author' => 'Willy Wonka',
            'publisher' => 'Gemoidia Barat',
            'year' => 2015,
            'description' => 'A book with lots of knowledge!',
        ],[
            'books_id' => 13,
            'author' => 'Unknown',
            'publisher' => 'Kompas Invisible',
            'year' => 2010,
            'description' => 'The only book with unknown author.',
        ],[
            'books_id' => 14,
            'author' => 'Wellington Daniel',
            'publisher' => 'Kompas Jam',
            'year' => 2011,
            'description' => 'Overall its a great book to read!',
        ],[
            'books_id' => 15,
            'author' => 'Werewolf',
            'publisher' => 'Kompas Anime',
            'year' => 2020,
            'description' => 'The best werewolf is here!',
        ],[
            'books_id' => 16,
            'author' => 'Jason Kenneth',
            'publisher' => 'Kompas Arahmana',
            'year' => 2021,
            'description' => 'The best motivational book ever!',
        ],[
            'books_id' => 17,
            'author' => 'Edwin Halim',
            'publisher' => 'Kompas Takberarah',
            'year' => 2018,
            'description' => 'You will never get bored with this!',
        ],[
            'books_id' => 18,
            'author' => 'Kenny Wijaya',
            'publisher' => 'Kompas Ilmu',
            'year' => 2016,
            'description' => 'The most interesting book ever!',
        ]]);
    }
}
