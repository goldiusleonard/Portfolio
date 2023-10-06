<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

class UserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     *
     * @return void
     */
    public function run()
    {
        DB::table('users')->insert(
            [
                'role_id' => 1,
                'gender_id' => 1,
                'first_name' => 'Goldius',
                'last_name' => 'Leonard',
                'email' => 'goldius.leonard@binus.ac.id',
                'password' => Hash::make('testing123'),
                'display_picture_link' => 'user_photos/goldius.leonard@binus.ac.id.jpg',
                'delete_flag' => false
            ]
        );

        DB::table('users')->insert(
            [
                'role_id' => 2,
                'gender_id' => 2,
                'first_name' => 'Maria',
                'middle_name' => 'Bellen',
                'last_name' => 'Christine',
                'email' => 'maria.bellen@binus.ac.id',
                'password' => Hash::make('testing123'),
                'display_picture_link' => 'user_photos/maria.bellen@binus.ac.id.png',
                'delete_flag' => false
            ]
        );
    }
}
