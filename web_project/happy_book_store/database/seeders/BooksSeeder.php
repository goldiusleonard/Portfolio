<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class BooksSeeder extends Seeder
{
    /**
     * Run the database seeds.
     *
     * @return void
     */
    public function run()
    {
        DB::table('books')->insert([[
            'categories_id' => 1,
            'title' => 'Someone Who cares',
        ],[
            'categories_id' => 1,
            'title' => 'Someone Who don\'t cares',
        ],[
            'categories_id' => 2,
            'title' => 'The Formula of Chemistry',
        ],[
            'categories_id' => 2,
            'title' => 'The Formula of Physics',
        ],[
            'categories_id' => 3,
            'title' => 'Theory of C++',
        ],[
            'categories_id' => 3,
            'title' => 'Theory of Java',
        ],[
            'categories_id' => 4,
            'title' => 'John Bowel: The Ruler',
        ],[
            'categories_id' => 4,
            'title' => 'King Thompson',
        ],[
            'categories_id' => 5,
            'title' => 'Pythagoras Theorem',
        ],[
            'categories_id' => 5,
            'title' => 'Matrix & Statistics',
        ],[
            'categories_id' => 6,
            'title' => 'Southeast Asia & East Asia',
        ],[
            'categories_id' => 6,
            'title' => 'North America & Latin America',
        ],[
            'categories_id' => 7,
            'title' => 'Barack Obama vs Donald Trump',
        ],[
            'categories_id' => 7,
            'title' => 'Donald Trump vs Joe Biden',
        ],[
            'categories_id' => 8,
            'title' => 'The Tapering Tantrum',
        ],[
            'categories_id' => 8,
            'title' => 'Macro & Micro Economics',
        ],[
            'categories_id' => 9,
            'title' => 'Boston Dynamics Innovations',
        ],[
            'categories_id' => 9,
            'title' => 'Google Technologies',
        ]]);
    }
}
