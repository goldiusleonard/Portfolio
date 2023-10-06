<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class EBook extends Model
{
    use HasFactory;

    public function orders() {
        return $this->hasMany(Order::class);
    }

    protected $fillable = [
        'title',
        'author',
        'description'
    ];
}
