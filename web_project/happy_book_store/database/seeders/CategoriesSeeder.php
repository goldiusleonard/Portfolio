<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class CategoriesSeeder extends Seeder
{
    /**
     * Run the database seeds.
     *
     * @return void
     */
    public function run()
    {
        DB::table('categories')->insert([[
            'category' => 'Fiction',
        ],[
            'category' => 'Science',
        ],[
            'category' => 'Computer',
        ],[
            'category' => 'Non-Fiction',
        ],[
            'category' => 'Math',
        ],[
            'category' => 'Geography',
        ],[
            'category' => 'Politics',
        ],[
            'category' => 'Economy',
        ],[
            'category' => 'Technology',
        ],[
            'category' => 'Cryptocurrency',
        ]]);
    }
}
